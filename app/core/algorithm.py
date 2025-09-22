from random import randint
from math import floor

from sqlmodel import (
    select,
    Session,
    col,
    SQLModel,
    text,
    desc,
    delete,
    and_,
    func,
    or_,
    not_,
)
from fastapi import HTTPException

from app.data.algorithm import *
from app.data.db import *
from app.data.public import *
from app.core.logger import logger
from app.core.config import settings

# TODO: types
# To improve performance, this program uses internal lists (pointers to objects).
# It's assumed that working without deserialization will increase performance and reduce memory usage.
# This leverages an internal by-reference protocol.
#
# plan_ref:
# |--------------|------------|----------------------------------------|
# | reference ID | default    | description                            |
# |--------------|------------|----------------------------------------|
# | 0            | False      | End the week loop                      |
# | 1            | False      | End the tech loop                      |
# | 2            | False      | End the subtech loop                   |
# | 3            | 0          | Week free time                         |
# | 4            | []         | Week exercises list                    |
# | 5            | 0          | Time for week                          |
# | 6            | 0          | Time for tech                          |
# | 7            | 0          | Time for subtech                       |
# | 8            | 0          | Time for normal part                   |
# | 9            | 0          | Time for old part                      |
# | 10           | 0          | Time for learning part                 |
# |--------------|------------|----------------------------------------|


class PlanCreator:
    def __init__(self, session: Session, player: int):
        self.session = session
        self.player = player

        self.init_constraints()

    def init_constraints(self):
        self.WEEK_COUNT = 13
        self.DEFAULT_PLAN_ID = 1

    async def init_internal_variables(self):
        self.used_techs = self.session.exec(
            select(TechSum)
            .where(col(TechSum.player) == self.player)
            .order_by(desc(TechSum.prozent))
        ).all()
        self.unused_techs = self.session.exec(
            select(TechSum)
            .where(
                and_(col(TechSum.player) == self.player),
                not_(col(TechSum.tech).in_(map(lambda x: x.tech, self.used_techs))),
            )
            .order_by(desc(TechSum.prozent))
        ).all()
        self.plan = Plan(
            player=self.player, start_date=datetime.now(), id=self.DEFAULT_PLAN_ID
        )
        self.session.add(self.plan)
        self.session.commit()
        self.session.refresh(self.plan)
        self.exercises = []

    async def create_plan(self):
        plan_ref: list
        normal_part_default = (
            percentages_for_exercises[0] / 100 * settings.MINUTES_IN_WEEK
        )
        old_part_default = percentages_for_exercises[1] / 100 * settings.MINUTES_IN_WEEK
        learning_part_default = (
            percentages_for_exercises[2] / 100 * settings.MINUTES_IN_WEEK
        )
        # set end_the_loop flag for week loop
        plan_ref[0] = False
        for week in range(1, self.WEEK_COUNT):
            # check end_the_loop flag
            if plan_ref[0]:
                break
            # init week variables
            percentages_for_exercises = settings.PERCENTAGE_EXERCISES[week - 1]
            plan_ref[3] = 0  # free_time
            plan_ref[4] = []  # week_exercises
            plan_ref[8] = normal_part_default  # normal_part
            plan_ref[9] = old_part_default  # old_part
            plan_ref[10] = learning_part_default  # learning_part
            plan_week = PlanWeek(
                player=self.player, plan=self.DEFAULT_PLAN_ID, week=week
            )
            self.session.add(plan_week)
            self.session.commit()
            self.session.refresh(plan_week)

            self.process_week(plan_week, plan_ref)

        self.session.commit()
        return self.plan

    async def process_week(self, plan_week: PlanWeek, plan_ref: list):
        """Process week

        week_references: local list, that will pass some information by reference
        """
        for tech in self.used_techs:
            # check end_the_loop flag
            if plan_ref[1]:
                break
            self.process_tech(plan_week, tech, True, plan_ref)

        self.exercises.append(plan_ref[4])

        for tech in self.unused_techs:
            # check end_the_loop flag
            if plan_ref[1]:
                break
            self.process_tech(plan_week, tech, False, plan_ref)

        if plan_week.week > 1:
            last_week_exercises = plan_ref[plan_week.week - 1]
            while old_part > 3:
                len_week_exercises = len(last_week_exercises[0])
                db_exercise = last_week_exercises[randint(0, len_week_exercises)]
                old_part -= db_exercise[1]
                db_exercise = db_exercise[0]
                max_id = (
                    self.session.exec(
                        select(func.max(PlanExercise.id)).where(
                            and_(
                                col(PlanExercise.player) == self.player,
                                col(PlanExercise.plan) == self.plan.id,
                                col(PlanExercise.week) == plan_week.week,
                            )
                        )
                    ).first()
                    or 0
                )
                db_exercise.id = max_id + 1
                self.session.add(db_exercise)

        free_time = floor(free_time)
        logger.debug("- FREE TIME: {}".format(free_time))

    async def process_tech(
        self, plan_week: PlanWeek, tech: Tech, used_tech: bool, plan_ref: list
    ):
        if plan_ref[1]:
            return
        for subtech in self.session.exec(
            select(SubtechSum)
            .where(
                and_(
                    col(SubtechSum.player) == self.player,
                    col(SubtechSum.tech) == tech.tech,
                )
            )
            .order_by(desc(SubtechSum.prozent))
        ).all():
            if used_tech:
                await self.process_used_subtech(plan_week, tech, subtech, plan_ref)
            else:
                await self.process_unused_subtech(plan_week, tech, subtech, plan_ref)

    async def process_used_subtech(
        self, plan_week: PlanWeek, tech: Tech, subtech: Subtech, plan_ref: list
    ):
        if plan_ref[2]:
            return
        plan_ref[7] = settings.MINUTES_IN_WEEK * subtech.prozent  # time_for_subtech
        plan_ref[3] += plan_ref[7] - floor(plan_ref[7])  # free_time
        plan_ref[7] = floor(plan_ref[7])  # time_for_subtech

        # check if the whole subtech <= 3 minutes
        if plan_ref[7] <= 3:
            free_time += plan_ref[7]
            return

        impacts = self.session.exec(
            select(ImpactSum).where(
                and_(
                    col(ImpactSum.player) == self.player,
                    col(ImpactSum.tech) == tech.tech,
                    col(ImpactSum.subtech) == subtech.subtech,
                )
            )
        ).all()
        if not impacts:
            return

        existing_impacts = list(map(lambda x: x.impact, impacts))

        def impact_exists(impact: Impact) -> bool:
            return impact in existing_impacts

        db_exercises = []
        # get exercises using week and impact as a parameter
        # also calculate the time for the impact
        if plan_week.week % 2 == 1:
            if impact_exists(Impact.FAIL) or impact_exists(Impact.MISTAKE):
                db_exercises = self.session.exec(
                    select(Exercise).where(
                        and_(
                            col(Exercise.tech) == tech.tech,
                            col(Exercise.subtech) == subtech.subtech,
                            or_(
                                col(Exercise.simulation_exercises) == True,
                                col(Exercise.exercises_with_the_ball_on_your_own)
                                == True,
                                col(Exercise.exercises_with_the_ball_in_pairs) == True,
                                # not_(col(Exercise.id).in_(planned_exercises)),
                            ),
                            col(Exercise.exercises_for_learning) == False,
                        )
                    )
                ).all()
        elif plan_week.week % 2 == 0:
            if impact_exists(Impact.EFFICIENCY) or impact_exists(Impact.SCORE):
                db_exercises = self.session.exec(
                    select(Exercise).where(
                        and_(
                            col(Exercise.tech) == tech.tech,
                            col(Exercise.subtech) == subtech.subtech,
                            or_(
                                col(Exercise.exercises_with_the_ball_in_pairs) == True,
                                col(Exercise.exercises_with_the_ball_in_groups) == True,
                                col(Exercise.exercises_in_difficult_conditions) == True,
                            ),
                            col(Exercise.exercises_for_learning) == False,
                        )
                    )
                ).all()

        exercise_counter = 0
        while time_for_subtech > 0:
            if end_the_loop:
                break
            # if we have no time to do this exercise or
            # we dont have any exercises -> free_time
            if time_for_subtech <= 3 or not db_exercises:
                free_time += time_for_subtech
                break

            exercise: Exercise = db_exercises.pop()

            # is shifted in 1 in the right direction
            # the harder one is in prio
            if (
                exercise.simulation_exercises
                or exercise.exercises_with_the_ball_on_your_own
            ):
                current_impact = Impact.FAIL
            elif exercise.exercises_with_the_ball_in_pairs:
                current_impact = Impact.MISTAKE
            elif exercise.exercises_with_the_ball_in_groups:
                current_impact = Impact.EFFICIENCY
            elif exercise.exercises_in_difficult_conditions:
                current_impact = Impact.SCORE

            if not impact_exists(current_impact):
                continue

            # add to planned exercises pool to ensure that we will
            # not have any dublicated in the future
            # planned_exercises.append(exercise.id)
            exercise_counter += 1
            time_for_subtech -= exercise.time_per_exercise
            # calculate best zone
            zone = self.session.exec(
                select(col(ZoneSum.zone), func.max(col(ZoneSum.prozent))).where(
                    and_(
                        col(ZoneSum.player) == self.player,
                        col(ZoneSum.tech) == tech.tech,
                        col(ZoneSum.subtech) == subtech.subtech,
                        col(ZoneSum.impact) == current_impact.name,
                    )
                )
            ).first()

            max_id = (
                self.session.exec(
                    select(func.max(PlanExercise.id)).where(
                        and_(
                            col(PlanExercise.player) == self.player,
                            col(PlanExercise.plan) == self.plan.id,
                            col(PlanExercise.week) == plan_week.week,
                        )
                    )
                ).first()
                or 0
            )
            db_exercise = PlanExercise(
                id=max_id + 1,
                player=self.player,
                plan=self.plan.id,
                week=plan_week.week,
                exercise=exercise.id,
                from_zone=int(zone.zone.split("-")[0]),
                to_zone=int(zone.zone.split("-")[1]),
            )
            normal_part -= exercise.time_per_exercise
            if normal_part <= 3:
                end_the_loop = True
            self.exercises.append((db_exercise, exercise.time_per_exercise))
            self.session.add(db_exercise)

    async def process_unused_subtech(
        self, plan_week: PlanWeek, tech: Tech, subtech: Subtech, plan_ref: list
    ):
        if plan_ref[2]:
            return
        plan_ref[7] = settings.MINUTES_IN_WEEK * subtech.prozent  # time_for_subtech
        plan_ref[3] += plan_ref[7] - floor(plan_ref[7])  # free_time
        plan_ref[7] = floor(plan_ref[7])  # time_for_subtech

        # check if the whole subtech <= 3 minutes
        if plan_ref[7] <= 3:
            free_time += plan_ref[7]
            return

        impacts = self.session.exec(
            select(ImpactSum).where(
                and_(
                    col(ImpactSum.player) == self.player,
                    col(ImpactSum.tech) == tech.tech,
                    col(ImpactSum.subtech) == subtech.subtech,
                )
            )
        ).all()
        if not impacts:
            return

        existing_impacts = list(map(lambda x: x.impact, impacts))

        def impact_exists(impact: Impact) -> bool:
            return impact in existing_impacts

        db_exercises = []
        # get exercises using week and impact as a parameter
        # also calculate the time for the impact
        if plan_week.week % 2 == 1:
            if impact_exists(Impact.FAIL) or impact_exists(Impact.MISTAKE):
                db_exercises = self.session.exec(
                    select(Exercise).where(
                        and_(
                            col(Exercise.tech) == tech.tech,
                            col(Exercise.subtech) == subtech.subtech,
                            or_(
                                col(Exercise.simulation_exercises) == True,
                                col(Exercise.exercises_with_the_ball_on_your_own)
                                == True,
                                col(Exercise.exercises_with_the_ball_in_pairs) == True,
                                # not_(col(Exercise.id).in_(planned_exercises)),
                            ),
                            col(Exercise.exercises_for_learning) == True,
                        )
                    )
                ).all()
        elif plan_week.week % 2 == 0:
            if impact_exists(Impact.EFFICIENCY) or impact_exists(Impact.SCORE):
                db_exercises = self.session.exec(
                    select(Exercise).where(
                        and_(
                            col(Exercise.tech) == tech.tech,
                            col(Exercise.subtech) == subtech.subtech,
                            or_(
                                col(Exercise.exercises_with_the_ball_in_pairs) == True,
                                col(Exercise.exercises_with_the_ball_in_groups) == True,
                                col(Exercise.exercises_in_difficult_conditions) == True,
                            ),
                            col(Exercise.exercises_for_learning) == True,
                        )
                    )
                ).all()

        exercise_counter = 0
        exercises = []
        while time_for_subtech > 0:
            if end_the_loop:
                break
            # if we have no time to do this exercise or
            # we dont have any exercises -> free_time
            if time_for_subtech <= 3 or not db_exercises:
                free_time += time_for_subtech
                break

            exercise: Exercise = db_exercises.pop()

            # is shifted in 1 in the right direction
            # the harder one is in prio
            if (
                exercise.simulation_exercises
                or exercise.exercises_with_the_ball_on_your_own
            ):
                current_impact = Impact.FAIL
            elif exercise.exercises_with_the_ball_in_pairs:
                current_impact = Impact.MISTAKE
            elif exercise.exercises_with_the_ball_in_groups:
                current_impact = Impact.EFFICIENCY
            elif exercise.exercises_in_difficult_conditions:
                current_impact = Impact.SCORE

            if not impact_exists(current_impact):
                continue

            # add to planned exercises pool to ensure that we will
            # not have any dublicated in the future
            # planned_exercises.append(exercise.id)
            exercise_counter += 1
            time_for_subtech -= exercise.time_per_exercise
            logger.debug(">5 -> exercise: {}".format(time_for_subtech))

            # calculate best zone
            zone = self.session.exec(
                select(col(ZoneSum.zone), func.max(col(ZoneSum.prozent))).where(
                    and_(
                        col(ZoneSum.player) == self.player,
                        col(ZoneSum.tech) == tech.tech,
                        col(ZoneSum.subtech) == subtech.subtech,
                        col(ZoneSum.impact) == current_impact.name,
                    )
                )
            ).first()

            max_id = (
                self.session.exec(
                    select(func.max(PlanExercise.id)).where(
                        and_(
                            col(PlanExercise.player) == self.player,
                            col(PlanExercise.plan) == self.plan.id,
                            col(PlanExercise.week) == plan_week.week,
                        )
                    )
                ).first()
                or 0
            )
            db_exercise = PlanExercise(
                id=max_id + 1,
                player=self.player,
                plan=self.plan.id,
                week=plan_week.week,
                exercise=exercise.id,
                from_zone=int(zone.zone.split("-")[0]),
                to_zone=int(zone.zone.split("-")[1]),
            )
            learning_part -= exercise.time_per_exercise
            if learning_part <= 3:
                end_the_loop = True
            exercises.append((db_exercise, exercise.time_per_exercise))
            self.session.add(db_exercise)
            self.week_exercises.append(exercises)

    async def tearwdown(self):
        """Teardown last known plan"""
        # teardown last plan TODO
        fk_status_result = self.session.exec(
            text("PRAGMA foreign_keys;")
        ).scalar_one_or_none()
        logger.debug(f"PRAGMA foreign_keys status before delete: {fk_status_result}")

        # teardown last plan if it exists
        existing_plan = self.session.exec(
            select(Plan).where(and_(col(Plan.player) == self.player, col(Plan.id) == 1))
        ).first()
        if existing_plan:
            self.session.exec(
                delete(Plan).where(
                    and_(col(Plan.player) == self.player, col(Plan.id) == 1)
                )
            )

        # teardown plan weeks
        plan_weeks = self.session.exec(
            select(PlanWeek).where(
                and_(col(PlanWeek.player) == self.player, col(PlanWeek.plan) == 1)
            )
        ).all()
        if plan_weeks:
            self.session.exec(
                delete(PlanWeek).where(
                    and_(col(PlanWeek.player) == self.player, col(PlanWeek.plan) == 1)
                )
            )
        self.session.commit()


async def calculate_sums(session: Session, player: int):
    # sums tierdown
    session.exec(delete(PlayerSum).where(col(PlayerSum.player) == player))
    session.exec(delete(TechSum).where(col(TechSum.player) == player))
    session.exec(delete(SubtechSum).where(col(SubtechSum.player) == player))
    session.exec(delete(ImpactSum).where(col(ImpactSum.player) == player))
    session.exec(delete(ZoneSum).where(col(ZoneSum.player) == player))
    session.commit()
    #
    player_sum = PlayerSum(player=player)
    session.add(player_sum)
    session.commit()
    session.refresh(player_sum)
    for action in session.exec(
        select(Action).where(col(Action.player) == player)
    ).all():
        player_sum.sum_actions += 1

        tech = session.get(Subtech, action.subtech).tech
        zone = str(action.from_zone) + "-" + str(action.to_zone)

        tech_sum = session.get(TechSum, (player, tech))
        print(tech_sum)
        if not tech_sum:
            tech_sum = TechSum(player=player, tech=tech)
            session.add(tech_sum)
            session.commit()
            session.refresh(tech_sum)

        tech_sum.sum_actions += 1

        subtech_sum = session.get(SubtechSum, (player, tech, action.subtech))
        if not subtech_sum:
            subtech_sum = SubtechSum(player=player, tech=tech, subtech=action.subtech)
            session.add(subtech_sum)
            session.commit()
            session.refresh(subtech_sum)

        subtech_sum.sum_actions += 1

        impact_sum = session.get(
            ImpactSum, (player, tech, action.subtech, action.impact.name)
        )
        if not impact_sum:
            impact_sum = ImpactSum(
                player=player,
                tech=tech,
                subtech=action.subtech,
                impact=action.impact.name,
            )
            session.add(impact_sum)
            session.commit()
            session.refresh(impact_sum)

        impact_sum.sum_actions += 1

        zone_sum = session.get(
            ZoneSum, (player, tech, action.subtech, action.impact.name, zone)
        )
        if not zone_sum:
            zone_sum = ZoneSum(
                player=player,
                tech=tech,
                subtech=action.subtech,
                impact=action.impact.name,
                zone=zone,
            )
            session.add(zone_sum)
            session.commit()
            session.refresh(zone_sum)
        zone_sum.sum_actions += 1
        session.add(player_sum)
        session.add(tech_sum)
        session.add(subtech_sum)
        session.add(impact_sum)
        session.add(zone_sum)
        session.commit()

    if player_sum.sum_actions == 0:
        session.close()
        raise HTTPException(status_code=404, detail="No actions found for player")
    calc_prozent(session, PlayerSum, player_sum.sum_actions, player)
    calc_prozent(session, TechSum, player_sum.sum_actions, player)
    calc_prozent(session, SubtechSum, player_sum.sum_actions, player)
    calc_prozent(session, ImpactSum, player_sum.sum_actions, player)
    calc_prozent(session, ZoneSum, player_sum.sum_actions, player)
    session.commit()
    session.close()


def calc_prozent(session: Session, model: SQLModel, total: int, player: int):
    for row in session.exec(select(model).where(col(model.player) == player)).all():
        row.prozent = row.sum_actions / total
        session.add(row)


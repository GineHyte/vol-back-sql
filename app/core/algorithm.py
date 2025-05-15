from sqlmodel import select, Session, col, SQLModel, desc, delete, and_, func, or_, not_
from fastapi import HTTPException
from math import floor

from app.data.algorithm import *
from app.data.db import *
from app.data.public import *
from app.core.logger import logger
from app.core.config import settings


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


async def create_plan(session: Session, player: int):
    # teardown last plan TODO
    session.exec(
        delete(Plan).where(and_(col(Plan.player) == player, col(Plan.id) == 1))
    )
    session.commit()
    plan = Plan(player=player, start_date=datetime.now(), id=1)
    for week in range(1, 13):
        free_time = 0
        planned_exercises = []
        plan_week = PlanWeek(player=player, plan=1, week=week)
        session.add(plan)
        session.add(plan_week)
        session.commit()
        session.refresh(plan)
        session.refresh(plan_week)

        for tech in session.exec(
            select(TechSum)
            .where(col(TechSum.player) == player)
            .order_by(desc(TechSum.prozent))
        ).all():
            for subtech in session.exec(
                select(SubtechSum)
                .where(
                    and_(
                        col(SubtechSum.player) == player,
                        col(SubtechSum.tech) == tech.tech,
                    )
                )
                .order_by(desc(SubtechSum.prozent))
            ).all():
                time_for_subtech = settings.MINUTES_IN_WEEK * subtech.prozent
                free_time += time_for_subtech - floor(time_for_subtech)
                time_for_subtech = floor(time_for_subtech)

                # check if the whole subtech <= 5 minutes
                if time_for_subtech <= 5:
                    free_time += time_for_subtech
                    continue

                impacts = session.exec(
                    select(ImpactSum).where(
                        and_(
                            col(ImpactSum.player) == player,
                            col(ImpactSum.tech) == tech.tech,
                            col(ImpactSum.subtech) == subtech.subtech,
                        )
                    )
                ).all()
                if not impacts:
                    continue

                impact_timings = {}

                for impact in impacts:
                    impact_timings[impact.impact] = (
                        settings.MINUTES_IN_WEEK * impact.prozent
                    )

                # sort the impact timings by value
                impact_timings = {
                    k: v
                    for k, v in sorted(impact_timings.items(), key=lambda item: item[1])
                }


                # get exercise using week and impact as a parameter
                if week % 4 == 1:
                    current_impact = Impact.FAIL
                    exercises = session.exec(
                        select(Exercise).where(
                            and_(
                                col(Exercise.tech) == tech.tech,
                                col(Exercise.subtech) == subtech.subtech,
                                or_(
                                    col(Exercise.simulation_exercises) == True,
                                    col(Exercise.exercises_with_the_ball_on_your_own)
                                    == True,
                                ),
                                not_(col(Exercise.id).in_(planned_exercises)),
                            )
                        )
                    ).all()
                elif week % 4 == 2:
                    current_impact = Impact.MISTAKE
                    exercises = session.exec(
                        select(Exercise).where(
                            and_(
                                col(Exercise.tech) == tech.tech,
                                col(Exercise.subtech) == subtech.subtech,
                                or_(
                                    col(Exercise.exercises_with_the_ball_on_your_own)
                                    == True,
                                    col(Exercise.exercises_with_the_ball_in_pairs)
                                    == True,
                                ),
                                not_(col(Exercise.id).in_(planned_exercises)),
                            )
                        )
                    ).all()
                elif week % 4 == 3:
                    current_impact = Impact.EFFICIENCY
                    exercises = session.exec(
                        select(Exercise).where(
                            and_(
                                col(Exercise.tech) == tech.tech,
                                col(Exercise.subtech) == subtech.subtech,
                                or_(
                                    col(Exercise.exercises_with_the_ball_in_pairs)
                                    == True,
                                    col(Exercise.exercises_with_the_ball_in_groups)
                                    == True,
                                ),
                                not_(col(Exercise.id).in_(planned_exercises)),
                            )
                        )
                    ).all()
                elif week % 4 == 0:
                    current_impact = Impact.SCORE
                    exercises = session.exec(
                        select(Exercise).where(
                            and_(
                                col(Exercise.tech) == tech.tech,
                                col(Exercise.subtech) == subtech.subtech,
                                or_(
                                    col(Exercise.exercises_with_the_ball_in_groups)
                                    == True,
                                    col(Exercise.exercises_in_difficult_conditions)
                                    == True,
                                ),
                                not_(col(Exercise.id).in_(planned_exercises)),
                            )
                        )
                    ).all()

                logger.debug(current_impact, str(current_impact))
                if current_impact not in impact_timings:
                    continue
                time_for_impact = impact_timings[current_impact]

                while time_for_impact > 0:
                    exercise_counter = 0
                    # if we have no time to do this exercise or
                    # we dont have any exercises -> free_time
                    if time_for_impact <= 5 or not exercises:
                        free_time += time_for_impact
                        time_for_subtech -= time_for_impact
                        break

                    exercise = exercises.pop()

                    # add to planned exercises pool to ensure that we will
                    # not have any dublicated in the future
                    planned_exercises.append(exercise.id)
                    exercise_counter += 1
                    time_for_subtech -= exercise.time_per_exercise
                    time_for_impact -= exercise.time_per_exercise

                    # calculate best zone
                    zone = session.exec(
                        select(col(ZoneSum.zone), func.max(col(ZoneSum.prozent))).where(
                            and_(
                                col(ZoneSum.player) == player,
                                col(ZoneSum.tech) == tech.tech,
                                col(ZoneSum.subtech) == subtech.subtech,
                                col(ZoneSum.impact) == current_impact,
                            )
                        )
                    ).first()

                    max_id = (
                        session.exec(
                            select(func.max(PlanExercise.id)).where(
                                and_(
                                    col(PlanExercise.player) == player,
                                    col(PlanExercise.plan) == plan.id,
                                    col(PlanExercise.week) == plan_week.week,
                                )
                            )
                        ).first()
                        or 0
                    )
                    exercise_db = PlanExercise(
                        id=max_id + 1,
                        player=player,
                        plan=plan.id,
                        week=plan_week.week,
                        exercise=exercise.id,
                        from_zone=int(zone.split("-")[0]),
                        to_zone=int(zone.split("-")[1]),
                    )
                    session.add(exercise_db)
    session.commit()
    free_time = floor(free_time)
    return plan

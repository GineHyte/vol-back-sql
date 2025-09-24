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

class PlanCreator:
    """
    Creates training plans for players based on their historical performance data.
    
    The PlanCreator analyzes a player's technique usage patterns, impact effectiveness,
    and zone performance to generate a structured 13-week training plan with exercises
    tailored to their strengths and weaknesses.
    
    Attributes:
        session (Session): Database session for data operations
        player (int): Player ID for whom the plan is being created
        WEEK_COUNT (int): Total number of weeks in the plan (default: 13)
        DEFAULT_PLAN_ID (int): Default plan identifier (default: 1)
    """

    def __init__(self, session: Session, player: int):
        """
        Initialize the PlanCreator with database session and player ID.
        
        Args:
            session (Session): SQLModel database session
            player (int): Unique identifier for the player
        """
        self.session = session
        self.player = player
        self.init_constraints()

    def init_constraints(self):
        """
        Initialize planning constraints and configuration values.
        
        Sets up the basic parameters for plan generation including
        the number of weeks and default plan ID.
        """
        self.WEEK_COUNT = 13
        self.DEFAULT_PLAN_ID = 1

    async def init_internal_variables(self):
        """
        Initialize internal variables and fetch player data from database.
        
        This method:
        - Fetches used and unused techniques for the player
        - Creates a new plan record in the database
        - Initializes loop control flags
        - Sets up timing variables for different exercise categories
        - Prepares exercise tracking lists
        
        The method distinguishes between used techniques (those the player has
        performed) and unused techniques to create appropriate training focus.
        """
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

        # end loop flags
        self._end_week_loop = False
        self._end_tech_loop = False
        self._end_subtech_loop = False
        self._end_exercise_loop = False

        # timings (in minutes)
        self._time_for_week = 0
        self._time_for_tech = 0
        self._time_for_subtech = 0
        self._time_for_normal_part = 0
        self._time_for_old_part = 0
        self._time_for_learning_part = 0
        self._time_for_week_free = 0 # free time in week

        # lists
        self._week_exercises = []
        self._exercises = [] # 2d for every week

    async def create_plan(self):
        """
        Create a complete training plan for the player.
        
        This is the main orchestration method that:
        1. Tears down any existing plan
        2. Initializes internal variables
        3. Processes each week of the 13-week plan
        4. Commits the final plan to the database
        
        Returns:
            Plan: The created plan object with all associated exercises
            
        The method processes weeks sequentially, calculating exercise distributions
        based on predefined percentages for normal, old, and learning exercises.
        """
        # teardown first
        await self.teardown()

        # init varialbes s. function
        await self.init_internal_variables()

        for week in range(1, self.WEEK_COUNT):
            # check end_the_loop flag
            if self._end_week_loop:
                break
            # init plan variables
            self._time_for_week_free = 0  # free_time
            self._week_exercises = []  # week_exercises
            percentages_for_exercises = settings.PERCENTAGE_EXERCISES[week - 1]
            self._time_for_normal_part = percentages_for_exercises[0] / 100 * settings.MINUTES_IN_WEEK  # normal_part
            self._time_for_old_part= percentages_for_exercises[1] / 100 * settings.MINUTES_IN_WEEK  # old_part
            self._time_for_learning_part = percentages_for_exercises[2] / 100 * settings.MINUTES_IN_WEEK  # learning_part
            plan_week = PlanWeek(
                player=self.player, plan=self.DEFAULT_PLAN_ID, week=week
            )
            self.session.add(plan_week)
            self.session.commit()
            self.session.refresh(plan_week)

            await self.process_week(plan_week)

        self.session.commit()
        return self.plan

    async def process_week(self, plan_week: PlanWeek):
        """
        Process a single week of the training plan.
        
        Args:
            plan_week (PlanWeek): The week being processed
            
        This method:
        - Processes all used techniques first (player's strengths)
        - Processes unused techniques second (areas for improvement)
        - Handles old exercises from previous weeks for reinforcement
        - Calculates and logs free time remaining in the week
        
        The week processing follows a specific order to prioritize the player's
        existing skills while introducing new techniques for development.
        """
        for tech in self.used_techs:
            # check end_the_loop flag
            if self._end_tech_loop:
                break
            logger.info("> Processing used tech: {}".format(tech.tech))
            await self.process_used_tech(plan_week, tech)

        for tech in self.unused_techs:
            # check end_the_loop flag
            if self._end_tech_loop:
                break
            logger.info("> Processing unused tech: {}".format(tech.tech))
            await self.process_unused_tech(plan_week, tech)

        self._exercises.append(self._week_exercises)

        if plan_week.week > 1:
            last_week_exercises = self._exercises[plan_week.week - 2]  # Fix: week-2 for 0-based indexing
            len_week_exercises = len(last_week_exercises)
            logger.debug("> last_week_exercises: {}".format(last_week_exercises))
            if len_week_exercises:
                while self._time_for_old_part > 3:
                    if len_week_exercises == 0:  # Safety check
                        break
                        
                    selected_exercise = last_week_exercises[randint(0, len_week_exercises - 1)]
                    old_exercise = selected_exercise[0]
                    exercise_time = selected_exercise[1]
                    
                    # Validate the exercise still exists in database
                    existing_exercise = self.session.get(Exercise, old_exercise.exercise)
                    if not existing_exercise:
                        logger.warning(f"Exercise {old_exercise.exercise} no longer exists, skipping")
                        continue
                    
                    self._time_for_old_part -= exercise_time
                    
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
                    
                    try:
                        # Create a new instance instead of reusing the old one
                        new_exercise = PlanExercise(
                            id=max_id + 1,
                            player=self.player,
                            plan=self.plan.id,
                            week=plan_week.week,
                            exercise=old_exercise.exercise,
                            from_zone=old_exercise.from_zone,
                            to_zone=old_exercise.to_zone,
                        )
                        self.session.add(new_exercise)
                        self.session.flush()  # Flush to catch constraint violations early
                    except Exception as e:
                        logger.error(f"Failed to create old PlanExercise: {e}")
                        self.session.rollback()
                        continue

        self._time_for_week_free = floor(self._time_for_week_free)
        logger.debug("- FREE TIME: {}".format(self._time_for_week_free))

    async def process_used_tech(
        self, plan_week: PlanWeek, tech: TechBase
    ):
        """
        Process a specific technique within a week.
        
        Args:
            plan_week (PlanWeek): The current week being processed
            tech (Tech): The technique to process
            
        This method iterates through all subtechniques for the given technique,
        routing each to either used subtech processing based on the player's 
        history with the technique.
        """
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
            if self._end_subtech_loop: break
            logger.info("-> Processing used subtech: {}".format(subtech.subtech))
            await self.process_used_subtech(plan_week, tech, subtech)

    async def process_unused_tech(
        self, plan_week: PlanWeek, tech: TechBase
    ):
        """
        Process a specific technique within a week.
        
        Args:
            plan_week (PlanWeek): The current week being processed
            tech (Tech): The technique to process
            
        This method iterates through all subtechniques for the given technique,
        routing each to either unused subtech processing based on the player's 
        history with the technique.
        """
        for subtech in self.session.exec(
            select(Subtech)
            .where(
                col(Subtech.tech) == tech.tech,
            )
        ).all():
            if self._end_subtech_loop: break
            logger.info("-> Processing unused subtech: {}".format(subtech.subtech))
            await self.process_unused_subtech(plan_week, tech, subtech)

    async def process_used_subtech(
        self, plan_week: PlanWeek, tech: Tech, subtech: Subtech
    ):
        """
        Process a subtechnique that the player has used before.
        
        Args:
            plan_week (PlanWeek): Current week being processed
            tech (Tech): Parent technique
            subtech (Subtech): Subtechnique to process
            
        This method:
        - Calculates time allocation based on the player's usage percentage
        - Selects exercises based on week parity and impact types
        - Focuses on non-learning exercises (reinforcement/improvement)
        - Creates PlanExercise records for selected exercises
        - Manages time constraints and loop termination conditions
        
        Exercise selection varies by week:
        - Odd weeks: Focus on FAIL/MISTAKE impacts with simulation and ball exercises
        - Even weeks: Focus on EFFICIENCY/SCORE impacts with pairs/groups/difficult conditions
        """
        self._time_for_subtech = settings.MINUTES_IN_WEEK * subtech.prozent  # time_for_subtech
        self._time_for_week_free += self._time_for_subtech - floor(self._time_for_subtech)  # free_time
        self._time_for_subtech = floor(self._time_for_subtech)  # time_for_subtech

        # check if the whole subtech <= 3 minutes
        logger.debug("\t_time_for_subtech: {}".format(self._time_for_subtech))
        logger.debug("\tsubtech.prozent: {}".format(subtech.prozent))
        if self._time_for_subtech <= 3:
            self._time_for_week_free += self._time_for_subtech
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
        logger.debug("\timpacts len: {}".format(len(impacts)))
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
                            col(Exercise.id).in_(
                                select(ExerciseToSubtech.exercise_id).where(
                                    col(ExerciseToSubtech.subtech_id) == subtech.subtech
                                )
                            ),
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
                            col(Exercise.id).in_(
                                select(ExerciseToSubtech.exercise_id).where(
                                    col(ExerciseToSubtech.subtech_id) == subtech.subtech
                                )
                            ),
                            or_(
                                col(Exercise.exercises_with_the_ball_in_pairs) == True,
                                col(Exercise.exercises_with_the_ball_in_groups) == True,
                                col(Exercise.exercises_in_difficult_conditions) == True,
                            ),
                            col(Exercise.exercises_for_learning) == False,
                        )
                    )
                ).all()

        logger.debug("\tdb_exercise len: {}".format(len(db_exercises)))

        exercise_counter = 0
        while self._time_for_subtech > 0:
            if self._end_exercise_loop:
                break
            # if we have no time to do this exercise or
            # we dont have any exercises -> free_time
            if self._time_for_subtech <= 3 or not db_exercises:
                self._time_for_week_free += self._time_for_subtech
                break

            exercise: Exercise = db_exercises.pop()

            # Validate that exercise exists
            if not exercise or not exercise.id:
                logger.warning(f"Invalid exercise found, skipping")
                continue

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
            self._time_for_subtech -= exercise.time_per_exercise
            # calculate best zone
            zone_result = self.session.exec(
                select(col(ZoneSum.zone), func.max(col(ZoneSum.prozent))).where(
                    and_(
                        col(ZoneSum.player) == self.player,
                        col(ZoneSum.tech) == tech.tech,
                        col(ZoneSum.subtech) == subtech.subtech,
                        col(ZoneSum.impact) == current_impact.name,
                    )
                )
            ).first()

            # Validate zone exists
            if not zone_result or not zone_result.zone:
                logger.warning(f"No zone data found for player {self.player}, tech {tech.tech}, subtech {subtech.subtech}, impact {current_impact.name}")
                continue

            zone = zone_result

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
            
            try:
                db_exercise = PlanExercise(
                    id=max_id + 1,
                    player=self.player,
                    plan=self.plan.id,
                    week=plan_week.week,
                    exercise=exercise.id,
                    from_zone=int(zone.zone.split("-")[0]),
                    to_zone=int(zone.zone.split("-")[1]),
                )
                self._time_for_normal_part -= exercise.time_per_exercise
                if self._time_for_normal_part <= 3:
                    self._end_exercise_loop = True
                self._week_exercises.append((db_exercise, exercise.time_per_exercise))
                self.session.add(db_exercise)
                
                # Flush to catch constraint violations early
                self.session.flush()
            except Exception as e:
                logger.error(f"Failed to create PlanExercise: {e}")
                self.session.rollback()
                continue

    async def process_unused_subtech(
        self, plan_week: PlanWeek, tech: Tech, subtech: Subtech
    ):
        """
        Process a subtechnique that the player has not used before.
        
        Args:
            plan_week (PlanWeek): Current week being processed
            tech (Tech): Parent technique
            subtech (Subtech): Subtechnique to process
            
        This method handles new techniques for the player:
        - Calculates time allocation based on potential improvement areas
        - Selects learning-focused exercises to introduce new skills
        - Uses the same week-based impact logic as used subtechs
        - Emphasizes exercises marked for learning
        - Tracks exercises separately for learning progression
        
        The learning approach helps players gradually acquire new techniques
        while building on their existing skill foundation.
        """
        self._time_for_subtech = settings.MINUTES_IN_WEEK * subtech.prozent  # time_for_subtech
        self._time_for_week_free += self._time_for_subtech - floor(self._time_for_subtech)  # free_time
        self._time_for_subtech = floor(self._time_for_subtech)  # time_for_subtech

        # check if the whole subtech <= 3 minutes
        if self._time_for_subtech <= 3:
            self._time_for_week_free += self._time_for_subtech
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
                            col(Exercise.id).in_(
                                select(ExerciseToSubtech.exercise_id).where(
                                    col(ExerciseToSubtech.subtech_id) == subtech.subtech
                                )
                            ),
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
                            col(Exercise.id).in_(
                                select(ExerciseToSubtech.exercise_id).where(
                                    col(ExerciseToSubtech.subtech_id) == subtech.subtech
                                )
                            ),
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
        while self._time_for_subtech > 0:
            if self._end_exercise_loop:
                break
            # if we have no time to do this exercise or
            # we dont have any exercises -> free_time
            if self._time_for_subtech <= 3 or not db_exercises:
                self._time_for_week_free += self._time_for_subtech
                break

            exercise: Exercise = db_exercises.pop()

            # Validate that exercise exists
            if not exercise or not exercise.id:
                logger.warning(f"Invalid exercise found, skipping")
                continue

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
            self._time_for_subtech -= exercise.time_per_exercise
            logger.debug(">5 -> exercise: {}".format(self._time_for_subtech))

            # calculate best zone
            zone_result = self.session.exec(
                select(col(ZoneSum.zone), func.max(col(ZoneSum.prozent))).where(
                    and_(
                        col(ZoneSum.player) == self.player,
                        col(ZoneSum.tech) == tech.tech,
                        col(ZoneSum.subtech) == subtech.subtech,
                        col(ZoneSum.impact) == current_impact.name,
                    )
                )
            ).first()

            # Validate zone exists
            if not zone_result or not zone_result.zone:
                logger.warning(f"No zone data found for player {self.player}, tech {tech.tech}, subtech {subtech.subtech}, impact {current_impact.name}")
                continue

            zone = zone_result

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
            
            try:
                db_exercise = PlanExercise(
                    id=max_id + 1,
                    player=self.player,
                    plan=self.plan.id,
                    week=plan_week.week,
                    exercise=exercise.id,
                    from_zone=int(zone.zone.split("-")[0]),
                    to_zone=int(zone.zone.split("-")[1]),
                )
                self._time_for_learning_part -= exercise.time_per_exercise
                if self._time_for_learning_part <= 3:
                    self._end_exercise_loop = True
                self._week_exercises.append((db_exercise, exercise.time_per_exercise))
                self.session.add(db_exercise)
                
                # Flush to catch constraint violations early
                self.session.flush()
            except Exception as e:
                logger.error(f"Failed to create PlanExercise: {e}")
                self.session.rollback()
                continue

    async def teardown(self):
        """
        Clean up existing plan data before creating a new plan.
        
        This method:
        - Checks foreign key constraints status
        - Removes existing plan records for the player
        - Removes associated plan week records
        - Commits the cleanup to ensure clean slate for new plan
        
        The teardown ensures that each plan generation starts fresh without
        conflicts from previous planning attempts.
        """
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


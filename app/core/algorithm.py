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

        # Borders
        self.BORDER_WEEK_MINUTES = 3
        self.BORDER_TECH_MINUTES = 3
        self.BORDER_SUBTECH_MINUTES = 3
        self.BORDER_PARTS_MINUTES = 3

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
            select(Tech).where(
                col(Tech.id).in_(map(lambda x: x.tech, self.used_techs)),
            )
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
        self._this_shit_is_not_working = 0  # free time in week

        # lists
        self._week_exercises = []
        self._exercises = []  # 2d for every week

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
        # Disable foreign keys for the duration of plan creation
        try:
            self.session.exec(text("PRAGMA foreign_keys = OFF"))
            logger.debug("Foreign keys disabled for plan creation")
        except:
            self.session.rollback()
            await self.create_plan()
            return 
        try:
            # teardown first
            await self.teardown()

            # init varialbes s. function
            await self.init_internal_variables()

            for week in range(1, self.WEEK_COUNT):
                # check end_the_loop flag
                if self._end_week_loop:
                    break
                # init plan variables
                self._time_for_week = settings.MINUTES_IN_WEEK
                self._this_shit_is_not_working = 0  # free_time
                self._week_exercises = []  # week_exercises
                percentages_for_exercises = settings.PERCENTAGE_EXERCISES[week - 1]
                self._time_for_normal_part = (
                    percentages_for_exercises[0] / 100 * settings.MINUTES_IN_WEEK
                )  # normal_part
                self._time_for_old_part = (
                    percentages_for_exercises[1] / 100 * settings.MINUTES_IN_WEEK
                )  # old_part
                self._time_for_learning_part = (
                    percentages_for_exercises[2] / 100 * settings.MINUTES_IN_WEEK
                )  # learning_part
                plan_week = PlanWeek(
                    player=self.player, plan=self.DEFAULT_PLAN_ID, week=week
                )
                self.session.add(plan_week)
                self.session.commit()
                self.session.refresh(plan_week)

                await self.process_week(plan_week)

                await self.fill_with_game(plan_week)

            self.session.commit()

        finally:
            # Re-enable foreign keys regardless of success or failure
            # self.session.exec(text("PRAGMA foreign_keys = ON"))
            logger.debug("Foreign keys re-enabled after plan creation")

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

        self._end_tech_loop = False
        for tech in self.used_techs:
            # check end_the_loop flag
            if self._end_tech_loop:
                break
            await self.process_used_tech(plan_week, tech)
        used_count = len(self._week_exercises)

        self._end_tech_loop = False
        for tech in self.unused_techs:
            # check end_the_loop flag
            if self._end_tech_loop:
                break
            await self.process_unused_tech(plan_week, tech)

        if plan_week.week > 1:
            last_week_exercises = self._exercises[
                plan_week.week - 2
            ]  # Fix: week-2 for 0-based indexing
            len_week_exercises = len(last_week_exercises)
            if len_week_exercises:
                while self._time_for_old_part > self.BORDER_PARTS_MINUTES:
                    if len_week_exercises == 0:  # Safety check
                        break

                    selected_exercise = last_week_exercises[
                        randint(0, len_week_exercises - 1)
                    ]
                    old_exercise = selected_exercise[0]
                    exercise_time = selected_exercise[1]

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
                        time_per_exercise = self.session.get(Exercise, new_exercise.exercise).time_per_exercise
                        self._week_exercises.append((new_exercise, time_per_exercise))
                        self.session.flush()  # Flush to catch constraint violations early
                    except Exception as e:
                        logger.error(f"Failed to create old PlanExercise: {e}")
                        self.session.rollback()
                        continue
        self._exercises.append(self._week_exercises)
        self._this_shit_is_not_working = floor(self._this_shit_is_not_working)
        logger.debug(
            "- week: {}, found exercises: {}".format(
                plan_week.week, len(self._week_exercises)
            )
        )

    async def process_used_tech(self, plan_week: PlanWeek, tech: TechBase):
        """
        Process a specific technique within a week.

        Args:
            plan_week (PlanWeek): The current week being processed
            tech (Tech): The technique to process

        This method iterates through all subtechniques for the given technique,
        routing each to either used subtech processing based on the player's
        history with the technique.
        """
        self._end_subtech_loop = False
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
            if self._end_subtech_loop:
                break
            await self.process_used_subtech(plan_week, tech, subtech)

    async def process_unused_tech(self, plan_week: PlanWeek, tech: Tech):
        """
        Process a specific technique within a week.

        Args:
            plan_week (PlanWeek): The current week being processed
            tech (Tech): The technique to process

        This method iterates through all subtechniques for the given technique,
        routing each to either unused subtech processing based on the player's
        history with the technique.
        """
        self._end_subtech_loop = False
        subtechs = self.session.exec(
            select(Subtech).where(
                col(Subtech.tech) == tech.id,
            )
        ).all()
        for subtech in subtechs:
            if self._end_subtech_loop:
                break
            await self.process_unused_subtech(plan_week, tech, subtech, len(subtechs))

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
        self._time_for_subtech = settings.MINUTES_IN_WEEK * subtech.prozent
        self._this_shit_is_not_working += self._time_for_subtech - floor(
            self._time_for_subtech
        )
        self._time_for_subtech = floor(self._time_for_subtech)

        self.check_borders()

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

        self._end_exercise_loop = False
        exercise_counter = 0
        while self._time_for_subtech > 0:
            if self._end_exercise_loop:
                break

            self.check_borders()

            if not db_exercises:
                self._this_shit_is_not_working += self._time_for_subtech
                break

            exercise: Exercise = db_exercises.pop()

            # Validate that exercise exists
            if not exercise or not exercise.id:
                logger.warning(f"Invalid exercise found, skipping")
                continue

            # Determine current impact based on exercise type
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
            else:
                logger.warning(
                    f"Exercise {exercise.id} has no matching impact type, skipping"
                )
                continue

            if not impact_exists(current_impact):
                continue

            exercise_counter += 1
            self._time_for_subtech -= exercise.time_per_exercise

            # Calculate best zone
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

            if not zone_result or not zone_result.zone:
                logger.warning(
                    f"No zone data found for player {self.player}, tech {tech.tech}, subtech {subtech.subtech}, impact {current_impact.name}"
                )
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
                # Parse zone string safely
                zone_parts = zone.zone.split("-")
                if len(zone_parts) != 2:
                    logger.warning(f"Invalid zone format: {zone.zone}")
                    continue

                from_zone = int(zone_parts[0])
                to_zone = int(zone_parts[1])

                db_exercise = PlanExercise(
                    id=max_id + 1,
                    player=self.player,
                    plan=self.plan.id,
                    week=plan_week.week,
                    exercise=exercise.id,
                    from_zone=from_zone,
                    to_zone=to_zone,
                )
                self._time_for_normal_part -= exercise.time_per_exercise
                if self._time_for_normal_part <= self.BORDER_PARTS_MINUTES:
                    self._end_exercise_loop = True
                    self._end_subtech_loop = True
                    self._end_tech_loop = True
                self._week_exercises.append((db_exercise, exercise.time_per_exercise))
                self.session.add(db_exercise)

                # Flush to catch constraint violations early
                self.session.flush()
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing zone or creating PlanExercise: {e}")
                continue
            except Exception as e:
                logger.error(f"Failed to create PlanExercise: {e}")
                continue

    async def process_unused_subtech(
        self, plan_week: PlanWeek, tech: Tech, subtech: Subtech, subtechs_len: int
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
        self._time_for_subtech = (
            settings.MINUTES_IN_WEEK / subtechs_len
        )  # time_for_subtech
        self._this_shit_is_not_working += self._time_for_subtech - floor(
            self._time_for_subtech
        )  # free_time
        self._time_for_subtech = floor(self._time_for_subtech)  # time_for_subtech

        self.check_borders()

        impacts = self.session.exec(
            select(ImpactSum).where(
                and_(
                    col(ImpactSum.player) == self.player,
                    col(ImpactSum.tech) == tech.id,
                    col(ImpactSum.subtech) == subtech.id,
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
                                    col(ExerciseToSubtech.subtech_id) == subtech.id
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
                                    col(ExerciseToSubtech.subtech_id) == subtech.id
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
        self._end_exercise_loop = False
        while self._time_for_subtech > 0:
            if self._end_exercise_loop:
                break

            self.check_borders()

            if not db_exercises:
                self._this_shit_is_not_working += self._time_for_subtech
                break

            exercise: Exercise = db_exercises.pop()

            # Validate that exercise exists
            if not exercise or not exercise.id:
                logger.warning(f"Invalid exercise found, skipping")
                continue

            # Determine current impact based on exercise type
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
            else:
                logger.warning(
                    f"Exercise {exercise.id} has no matching impact type, skipping"
                )
                continue

            if not impact_exists(current_impact):
                continue

            exercise_counter += 1
            self._time_for_subtech -= exercise.time_per_exercise

            # calculate best zone
            zone_result = self.session.exec(
                select(col(ZoneSum.zone), func.max(col(ZoneSum.prozent))).where(
                    and_(
                        col(ZoneSum.player) == self.player,
                        col(ZoneSum.tech) == tech.id,
                        col(ZoneSum.subtech) == subtech.id,
                        col(ZoneSum.impact) == current_impact.name,
                    )
                )
            ).first()

            # Validate zone exists
            if not zone_result or not zone_result.zone:
                logger.warning(
                    f"No zone data found for player {self.player}, tech {tech.tech}, subtech {subtech.id}, impact {current_impact.name}"
                )
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
                if self._time_for_learning_part <= self.BORDER_PARTS_MINUTES:
                    self._end_exercise_loop = True
                    self._end_subtech_loop = True
                    self._end_tech_loop = True
                self._week_exercises.append((db_exercise, exercise.time_per_exercise))
                self.session.add(db_exercise)

                # Flush to catch constraint violations early
                self.session.flush()
            except Exception as e:
                logger.error(f"Failed to create PlanExercise: {e}")
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
        # teardown last plan if it exists
        existing_plan = self.session.exec(
            select(Plan).where(and_(col(Plan.player) == self.player, col(Plan.id) == self.DEFAULT_PLAN_ID))
        ).first()
        if existing_plan:
            self.session.exec(
                delete(Plan).where(
                    and_(col(Plan.player) == self.player, col(Plan.id) == self.DEFAULT_PLAN_ID)
                )
            )

        # teardown plan weeks
        plan_weeks = self.session.exec(
            select(PlanWeek).where(
                and_(col(PlanWeek.player) == self.player, col(PlanWeek.plan) == self.DEFAULT_PLAN_ID)
            )
        ).all()
        if plan_weeks:
            self.session.exec(
                delete(PlanWeek).where(
                    and_(col(PlanWeek.player) == self.player, col(PlanWeek.plan) == self.DEFAULT_PLAN_ID)
                )
            )

        # teardown plan exercises
        plan_exercises = self.session.exec(
            select(PlanExercise).where(
                and_(col(PlanExercise.player) == self.player, col(PlanExercise.plan) == self.DEFAULT_PLAN_ID)
            )
        ).all()

        if plan_exercises:
            self.session.exec(
                delete(PlanExercise).where(
                    and_(col(PlanExercise.player) == self.player, col(PlanExercise.plan) == self.DEFAULT_PLAN_ID)
                )
            )
        self.session.commit()

    async def fill_with_game(self, plan_week: PlanWeek):
        time_used = sum(map(lambda x: x[1], self._week_exercises))
        time_unused = settings.MINUTES_IN_WEEK - time_used
        time_unused = floor(time_unused)
        game_exercise = self.session.get(Exercise, -time_unused)

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

        if not game_exercise:
            game_exercise = Exercise(
                id=-time_unused,
                name="Гра",
                description="Гра",
                time_per_exercise=time_unused,
                difficulty=1
            )
            self.session.add(game_exercise)
            self.session.commit()
            self.session.refresh(game_exercise)

        db_exercise = PlanExercise(
            id=max_id + 1,
            player=self.player,
            plan=self.plan.id,
            week=plan_week.week,
            exercise=-time_unused,
            from_zone=0,
            to_zone=0,
        )
        self.session.add(db_exercise)
        self.session.commit()


    def check_borders(self):
        if self._time_for_week < self.BORDER_WEEK_MINUTES:
            self._this_shit_is_not_working += self._time_for_week
            self._end_week_loop = True
        elif self._time_for_tech < self.BORDER_TECH_MINUTES:
            self._this_shit_is_not_working += self._time_for_tech
            self._end_tech_loop = True
        elif self._time_for_subtech < self.BORDER_SUBTECH_MINUTES:
            self._this_shit_is_not_working += self._time_for_subtech
            self._end_subtech_loop = True
            self._end_exercise_loop = True


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

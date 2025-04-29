from sqlmodel import select, Session, col, SQLModel, desc, delete, and_, func
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
        logger.debug(player_sum)
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


def calc_prozent(sesion: Session, model: SQLModel, total: int, player: int):
    for row in sesion.exec(select(model).where(col(model.player) == player)).all():
        row.prozent = row.sum_actions / total
        sesion.add(row)


async def create_plan(session: Session, player: int):
    # teardown last plan TODO
    session.exec(
        delete(Plan).where(and_(col(Plan.player) == player, col(Plan.id) == 1))
    )
    session.exec(
        delete(PlanWeek).where(
            and_(col(PlanWeek.player) == player, col(PlanWeek.plan) == 1),
            col(PlanWeek.week) == 1,
        )
    )
    session.exec(
        delete(PlanExercise).where(
            and_(col(PlanExercise.player) == player, col(PlanExercise.plan) == 1),
            col(PlanExercise.week) == 1
        )
    )
    #
    free_time = 0
    exercise_pool = []
    planned_exercises = []
    plan = Plan(player=player, start_date=datetime.now(), id=1)
    plan_week = PlanWeek(player=player, plan=1, week=1)
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
                    col(SubtechSum.player) == player, col(SubtechSum.tech) == tech.tech
                )
            )
            .order_by(desc(SubtechSum.prozent))
        ).all():
            time_for_subtech = settings.MINUTES_IN_WEEK * subtech.prozent
            free_time += time_for_subtech - floor(time_for_subtech)
            time_for_subtech = floor(time_for_subtech)
            logger.debug(
                f"SubTech {subtech.subtech}, {time_for_subtech} min {'- skip' if time_for_subtech <= 5 else ''}"
            )

            if time_for_subtech <= 5:
                free_time += time_for_subtech
                time_for_subtech = -1
            while time_for_subtech > 0:
                exercises = session.exec(
                    select(Exercise).where(col(Exercise.subtech) == subtech.subtech)
                ).all()
                found = False
                for exercise in exercises:
                    if exercise.id not in exercise_pool:
                        found = True
                        exercise_pool.append(exercise.id)
                        planned_exercises.append(exercise)
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
                        )
                        session.add(exercise_db)
                        time_for_subtech -= exercise.time_per_exercise
                        break
                if not found:
                    break
    session.commit()
    free_time = floor(free_time)
    logger.debug(f"free time: {free_time}")
    return plan

from sqlmodel import select, Session, col, SQLModel, delete, and_
from fastapi import APIRouter, HTTPException, Depends

from app.core.db import get_session
from app.data.algorithm import *
from app.data.db import *
from app.data.public import *
from app.core.logger import logger
from app.data.utils import Status, Impact
from app.core.algorithm import calculate_sums, create_plan

router = APIRouter()


@router.get("/stats/calculate/{player_id}")
async def calculate_stats_player(
    player_id: int, session: CoachSession = Depends(get_session)
):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Calculate stats
    await calculate_sums(session, player_id)

    # Return stats
    return Status(status="success", detail="Stats calculated successfully")


@router.get("/stats/{player_id}")
async def get_stats_player(player_id: int, session: CoachSession = Depends(get_session)):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Get stats
    player_sum_db = session.exec(
        select(PlayerSum).where(col(PlayerSum.player) == player_id)
    ).first()
    tech_top_rows = session.exec(
        select(TechSum)
        .where(col(TechSum.player) == player_id)
        .order_by(col(TechSum.prozent).desc())
    ).all()

    # Create the public model with the correct NameWithId object
    player_sum = PlayerSumPublic(
        **player_sum_db.model_dump(exclude=["player"]),
        player=NameWithId(
            id=player.id, name="{} {}".format(player.first_name, player.last_name)
        ),
    )

    # For tech top, we need to batch fetch the tech names
    tech_ids = [ts.tech for ts in tech_top_rows]
    techs = {
        tech.id: tech
        for tech in session.exec(select(Tech).where(Tech.id.in_(tech_ids))).all()
    }

    tech_sums = []
    for ts in tech_top_rows:
        # Get tech name from our batch-fetched dict
        tech = techs.get(ts.tech)
        tech_sums.append(
            TechSumPublic(
                **ts.model_dump(exclude=["tech"]),
                tech=NameWithId(id=ts.tech, name=tech.name if tech else "Unknown"),
            )
        )

    # Return stats
    return {
        "player_sum": player_sum,
        "tech_top": tech_sums,
    }


@router.get("/stats/{player_id}/{tech_id}")
async def get_stats_tech(
    player_id: int, tech_id: int, session: CoachSession = Depends(get_session)
):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    tech = session.get(Tech, tech_id)
    if not tech:
        raise HTTPException(status_code=404, detail="Tech not found")

    # Get stats
    tech_top_db = session.exec(
        select(TechSum)
        .where(col(TechSum.player) == player_id)
        .where(col(TechSum.tech) == tech_id)
    ).first()
    subtech_top_rows = session.exec(
        select(SubtechSum)
        .where(col(SubtechSum.player) == player_id)
        .where(col(SubtechSum.tech) == tech_id)
        .order_by(col(SubtechSum.prozent).desc())
    ).all()

    # Create the public model with the correct NameWithId object
    tech_top = TechSumPublic(
        **tech_top_db.model_dump(exclude=["tech"]),
        tech=NameWithId(id=tech.id, name=tech.name),
    )

    # For subtech top, we need to batch fetch the tech names
    subtech_ids = [ss.subtech for ss in subtech_top_rows]
    subtechs = {
        subtech.id: subtech
        for subtech in session.exec(
            select(Subtech).where(Subtech.id.in_(subtech_ids))
        ).all()
    }

    subtech_top = []
    for ss in subtech_top_rows:
        # Get tech name from our batch-fetched dict
        subtech = subtechs.get(ss.subtech)
        subtech_top.append(
            SubtechSumPublic(
                **ss.model_dump(exclude=["subtech"]),
                subtech=NameWithId(
                    id=ss.subtech, name=subtech.name if subtech else "Unknown"
                ),
            )
        )

    # Return stats
    return {
        "tech_top": tech_top,
        "subtech_top": subtech_top,
    }


@router.get("/stats/{player_id}/{tech_id}/{subtech_id}")
async def get_stats_subtech(
    player_id: int,
    tech_id: int,
    subtech_id: int,
    session: CoachSession = Depends(get_session),
):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    tech = session.get(Tech, tech_id)
    if not tech:
        raise HTTPException(status_code=404, detail="Tech not found")

    subtech = session.get(Subtech, subtech_id)
    if not subtech:
        raise HTTPException(status_code=404, detail="Subtech not found")

    # Get stats
    subtech_top_db = session.exec(
        select(SubtechSum)
        .where(col(SubtechSum.player) == player_id)
        .where(col(SubtechSum.tech) == tech_id)
        .where(col(SubtechSum.subtech) == subtech_id)
    ).first()
    impact_top_rows = session.exec(
        select(ImpactSum)
        .where(col(ImpactSum.player) == player_id)
        .where(col(ImpactSum.tech) == tech_id)
        .where(col(ImpactSum.subtech) == subtech_id)
        .order_by(col(ImpactSum.prozent).desc())
    ).all()

    # Create the public model with the correct NameWithId object
    subtech_top = SubtechSumPublic(
        **subtech_top_db.model_dump(exclude=["subtech"]),
        subtech=NameWithId(id=subtech.id, name=subtech.name),
    )

    # Return stats
    return {
        "subtech_top": subtech_top,
        "impact_top": impact_top_rows,
    }


@router.get("/stats/{player_id}/{tech_id}/{subtech_id}/{impact}")
async def get_stats_impact(
    player_id: int,
    tech_id: int,
    subtech_id: int,
    impact: str,
    session: CoachSession = Depends(get_session),
):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    tech = session.get(Tech, tech_id)
    if not tech:
        raise HTTPException(status_code=404, detail="Tech not found")

    subtech = session.get(Subtech, subtech_id)
    if not subtech:
        raise HTTPException(status_code=404, detail="Subtech not found")

    impact = impact.upper()
    if impact in [item.value.upper() for item in Impact]:
        logger.debug(f"{impact} is a valid Impact enum value.")
    else:
        logger.debug(f"{impact} is not a valid Impact enum value.")
        raise HTTPException(status_code=404, detail="Impact not found")

    # Get stats
    impact_top = session.exec(
        select(ImpactSum)
        .where(col(ImpactSum.player) == player_id)
        .where(col(ImpactSum.tech) == tech_id)
        .where(col(ImpactSum.subtech) == subtech_id)
        .where(col(ImpactSum.impact) == impact)
    ).first()
    zone_top_rows = session.exec(
        select(ZoneSum)
        .where(col(ZoneSum.player) == player_id)
        .where(col(ZoneSum.tech) == tech_id)
        .where(col(ZoneSum.subtech) == subtech_id)
        .where(col(ZoneSum.impact) == impact)
        .order_by(col(ZoneSum.prozent).desc())
    ).all()

    # Return stats
    return {
        "impact_top": impact_top,
        "zone_top": zone_top_rows,
    }


@router.get("/plan/{player_id}")
async def generate_plan_player(
    player_id: int,
    session: CoachSession = Depends(get_session),
):
    player = session.get(Player, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    await create_plan(session, player_id)
    return Status(status="success", detail="Plan generated successfully")


@router.get("/plan/{player_id}/{week_number}")
async def get_plan_player_week(
    player_id: int,
    week_number: int,
    session: CoachSession = Depends(get_session),
):
    player_plan = session.get(Plan, (player_id, 1))
    if not player_plan:
        raise HTTPException(status_code=404, detail="Player or PlayerPlan not found")

    plan_week = session.get(PlanWeek, (player_id, 1, week_number))
    if not plan_week:
        raise HTTPException(status_code=404, detail="Plan for this week not found")

    plan_week_public = PlanWeekPublic(week=week_number, exercises=[])

    for plan_exercise in session.exec(
        select(PlanExercise).where(
            and_(
                col(PlanExercise.player) == player_id,
                col(PlanExercise.week) == week_number,
            )
        )
    ).all():
        db_exercise = session.get(Exercise, plan_exercise.exercise)
        exercise = ExercisePublic(**db_exercise.model_dump(exclude=["subtech", "tech"]))
        exercise.subtech = NameWithId(
            id=db_exercise.subtech, name=session.get(Subtech, db_exercise.subtech).name
        )
        exercise.tech = NameWithId(
            id=db_exercise.tech, name=session.get(Tech, db_exercise.tech).name
        )
        plan_week_public.exercises.append(exercise)

    return plan_week_public
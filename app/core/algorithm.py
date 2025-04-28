from sqlmodel import select, Session, col, SQLModel, desc, delete
from fastapi import HTTPException

from app.data.algorithm import *
from app.data.db import *
from app.data.public import *
from app.core.logger import logger


async def calculate_sums(session: Session, player: int):
    # sums tierdown
    session.exec(delete(PlayerSum).where(col(PlayerSum.player) == player))
    # session.exec(delete(TechSum).where(col(PlayerSum.player) == player))
    # session.exec(delete(SubtechSum).where(col(PlayerSum.player) == player))
    # session.exec(delete(ImpactSum).where(col(PlayerSum.player) == player))
    # session.exec(delete(ZoneSum).where(col(PlayerSum.player) == player))
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
    calc_prozent(session, player_sum, player_sum.sum_actions)
    calc_prozent(session, tech_sum, player_sum.sum_actions)
    calc_prozent(session, SubtechSum, player_sum.sum_actions)
    calc_prozent(session, ImpactSum, player_sum.sum_actions)
    calc_prozent(session, ZoneSum, player_sum.sum_actions)
    session.commit()
    session.close()


def calc_prozent(sesion: Session, model: SQLModel, total: int):
    for row in sesion.exec(select(model)).all():
        row.prozent = row.sum_actions / total
        sesion.add(row)


async def create_plan(session: Session, player: int):
    player_sum = session.get(PlayerSum, player)
    for tech in session.exec(
        select(TechSum).where(TechSum.player == player).order_by(desc(TechSum.prozent))
    ).all():
        logger.debug(f"{tech.tech}, {tech.prozent}")

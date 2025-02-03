from sqlmodel import select, Session, col, SQLModel, delete

from app.core.db import get_session
from app.data.algorithm import *
from app.data.db import *
from app.core.logger import logger

async def calculate_sums(session: Session, player: int): 
    session.exec(delete(PlayerSum))
    session.exec(delete(TechSum))
    session.exec(delete(SubtechSum))
    session.exec(delete(ImpactSum))
    session.exec(delete(ZoneSum))
    player_sum = session.get(PlayerSum, player)
    if player_sum is None:
        player_sum = PlayerSum(player=player)
        session.add(player_sum)
        session.commit()
        session.refresh(player_sum)
    for action in session.exec(select(Action).where(col(Action.player) == player)).all():
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

        impact_sum = session.get(ImpactSum, (player, tech, action.subtech, action.impact.name))
        if not impact_sum: 
            impact_sum = ImpactSum(player=player, tech=tech, subtech=action.subtech, impact=action.impact.name)
            session.add(impact_sum)
            session.commit()
            session.refresh(impact_sum)
            
        impact_sum.sum_actions += 1
        
        zone_sum = session.get(ZoneSum, (player, tech, action.subtech, action.impact.name, zone))
        if not zone_sum: 
            zone_sum = ZoneSum(player=player, tech=tech, subtech=action.subtech, impact=action.impact.name, zone=zone)
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
    calc_prozent(session, PlayerSum, player_sum.sum_actions)
    calc_prozent(session, TechSum, player_sum.sum_actions)
    calc_prozent(session, SubtechSum, player_sum.sum_actions)
    calc_prozent(session, ImpactSum, player_sum.sum_actions)
    calc_prozent(session, ZoneSum, player_sum.sum_actions)
    session.commit()
    session.close()

def calc_prozent(sesion: Session, model: SQLModel, total: int):
    for row in sesion.exec(select(model)).all():
        row.prozent = row.sum_actions / total
        sesion.add(row)
        
async def block4(session: Session, player: int):
    calculate_sums(session, player)
    tech_top = session.exec(select(TechSum).where(col(TechSum.player) == player).order_by(col(TechSum.prozent).desc())).all()
    subtech_top = session.exec(select(SubtechSum).where(col(SubtechSum.player) == player).order_by(col(SubtechSum.prozent).desc())).all()
    impact_top = session.exec(select(ImpactSum).where(col(ImpactSum.player) == player).order_by(col(ImpactSum.prozent).desc())).all()
    zone_top = session.exec(select(ZoneSum).where(col(ZoneSum.player) == player).order_by(col(ZoneSum.prozent).desc())).all()
    print("Tech top:", tech_top)
    print("Subtech top:", subtech_top)
    print("Impact top:", impact_top)
    print("Zone top:", zone_top)
    return tech_top, subtech_top, impact_top, zone_top

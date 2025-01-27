from sqlmodel import select, Session, col, SQLModel, delete

from app.core.db import get_session
from app.data.algorithm import *
from app.data.db import *
from app.core.logger import logger

async def calculate_sums(session: Session, player_id: int): 
    session.exec(delete(PlayerSum))
    session.exec(delete(TechSum))
    session.exec(delete(SubtechSum))
    session.exec(delete(ImpactSum))
    session.exec(delete(ZoneSum))
    player_sum = session.get(PlayerSum, player_id)
    if player_sum is None:
        player_sum = PlayerSum(player_id=player_id)
        session.add(player_sum)
        session.commit()
        session.refresh(player_sum)
    for action in session.exec(select(Action).where(col(Action.player) == player_id)).all():
        logger.debug(player_sum)
        player_sum.sum_actions += 1
        
        tech_id = session.get(Subtech, action.subtech).tech_id
        zone_id = str(action.from_zone) + "-" + str(action.to_zone)

        tech_sum = session.get(TechSum, (player_id, tech_id))
        print(tech_sum)
        if not tech_sum: 
            tech_sum = TechSum(player_id=player_id, tech_id=tech_id)
            session.add(tech_sum)
            session.commit()
            session.refresh(tech_sum)
            
        tech_sum.sum_actions += 1
        
        subtech_sum = session.get(SubtechSum, (player_id, tech_id, action.subtech))
        if not subtech_sum: 
            subtech_sum = SubtechSum(player_id=player_id, tech_id=tech_id, subtech_id=action.subtech)
            session.add(subtech_sum)
            session.commit()
            session.refresh(subtech_sum)
        
        subtech_sum.sum_actions += 1

        impact_sum = session.get(ImpactSum, (player_id, tech_id, action.subtech, action.impact.name))
        if not impact_sum: 
            impact_sum = ImpactSum(player_id=player_id, tech_id=tech_id, subtech_id=action.subtech, impact=action.impact.name)
            session.add(impact_sum)
            session.commit()
            session.refresh(impact_sum)
            
        impact_sum.sum_actions += 1
        
        zone_sum = session.get(ZoneSum, (player_id, tech_id, action.subtech, action.impact.name, zone_id))
        if not zone_sum: 
            zone_sum = ZoneSum(player_id=player_id, tech_id=tech_id, subtech_id=action.subtech, impact=action.impact.name, zone=zone_id)
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
        
async def block4(session: Session, player_id: int):
    calculate_sums(session, player_id)
    tech_top = session.exec(select(TechSum).where(col(TechSum.player_id) == player_id).order_by(col(TechSum.prozent).desc())).all()
    subtech_top = session.exec(select(SubtechSum).where(col(SubtechSum.player_id) == player_id).order_by(col(SubtechSum.prozent).desc())).all()
    impact_top = session.exec(select(ImpactSum).where(col(ImpactSum.player_id) == player_id).order_by(col(ImpactSum.prozent).desc())).all()
    zone_top = session.exec(select(ZoneSum).where(col(ZoneSum.player_id) == player_id).order_by(col(ZoneSum.prozent).desc())).all()
    print("Tech top:", tech_top)
    print("Subtech top:", subtech_top)
    print("Impact top:", impact_top)
    print("Zone top:", zone_top)
    return tech_top, subtech_top, impact_top, zone_top

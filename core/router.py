from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from common.models import Affiliate, Lead
from common.schemas import LeadAggregation
from common.security import get_current_affiliate

router = APIRouter()


@router.get("/leads", response_model=list[LeadAggregation])
async def get_leads_analytics(
    _affiliate: Affiliate = Depends(get_current_affiliate),
    db: AsyncSession = Depends(get_db),
) -> list[LeadAggregation]:
    result = await db.execute(
        select(
            Lead.affiliate_id,
            Lead.offer_id,
            func.count(Lead.id).label("total"),
        ).group_by(Lead.affiliate_id, Lead.offer_id)
    )
    rows = result.all()
    return [
        LeadAggregation(
            affiliate_id=row.affiliate_id,
            offer_id=row.offer_id,
            total=row.total,
        )
        for row in rows
    ]

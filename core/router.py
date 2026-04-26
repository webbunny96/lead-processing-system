from datetime import date as dt_date, datetime, time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from common.models import Affiliate, Lead
from common.schemas import ErrorResponse, LeadGroupByDate, LeadGroupByOffer, LeadOut
from common.security import get_current_affiliate

router = APIRouter(tags=["Leads analytics"])


@router.get(
    "/leads",
    response_model=list[LeadGroupByDate | LeadGroupByOffer],
    summary="Get leads analytics",
    description=(
        "Returns leads for the authenticated affiliate within date range. "
        "Use `group=date` to aggregate by day, or `group=offer` to aggregate by offer."
    ),
    responses={
        200: {"description": "Analytics result for selected aggregation mode."},
        401: {"model": ErrorResponse, "description": "Missing/invalid JWT or unknown affiliate."},
        422: {
            "description": (
                "Validation error for query params or custom range check "
                "when date_from is later than date_to."
            )
        },
    },
)
async def get_leads_analytics(
    date_from: dt_date = Query(
        ...,
        description="Start date, inclusive (YYYY-MM-DD).",
        examples=["2026-04-01"],
    ),
    date_to: dt_date = Query(
        ...,
        description="End date, inclusive (YYYY-MM-DD).",
        examples=["2026-04-30"],
    ),
    group: Literal["date", "offer"] = Query(
        ...,
        description="Aggregation mode.",
        examples=["date"],
    ),
    affiliate: Affiliate = Depends(get_current_affiliate),
    db: AsyncSession = Depends(get_db),
) -> list[LeadGroupByDate | LeadGroupByOffer]:
    if date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from cannot be later than date_to")

    from_dt = datetime.combine(date_from, time.min)
    to_dt = datetime.combine(date_to, time.max)

    result = await db.execute(
        select(Lead)
        .where(
            Lead.affiliate_id == affiliate.id,
            Lead.created_at >= from_dt,
            Lead.created_at <= to_dt,
        )
        .order_by(Lead.created_at.asc())
    )
    leads = result.scalars().all()

    if group == "date":
        grouped: dict[dt_date, list[LeadOut]] = {}
        for lead in leads:
            key = lead.created_at.date()
            grouped.setdefault(key, []).append(
                LeadOut(
                    id=lead.id,
                    affiliate_id=lead.affiliate_id,
                    offer_id=lead.offer_id,
                    name=lead.name,
                    phone=lead.phone,
                    country=lead.country,
                    created_at=lead.created_at,
                )
            )
        return [
            LeadGroupByDate(
                date=group_key,
                count=len(group_leads),
                leads=group_leads,
            )
            for group_key, group_leads in sorted(grouped.items(), key=lambda item: item[0])
        ]

    grouped_by_offer: dict[int, list[LeadOut]] = {}
    for lead in leads:
        grouped_by_offer.setdefault(lead.offer_id, []).append(
            LeadOut(
                id=lead.id,
                affiliate_id=lead.affiliate_id,
                offer_id=lead.offer_id,
                name=lead.name,
                phone=lead.phone,
                country=lead.country,
                created_at=lead.created_at,
            )
        )

    return [
        LeadGroupByOffer(
            offer_id=offer_id,
            count=len(group_leads),
            leads=group_leads,
        )
        for offer_id, group_leads in sorted(grouped_by_offer.items(), key=lambda item: item[0])
    ]

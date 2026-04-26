from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db
from common.models import Affiliate, Offer
from common.schemas import ErrorResponse, LeadCreate, LeadQueueMessage, StatusResponse
from common.security import get_current_affiliate
from landings.redis_client import enqueue_lead

router = APIRouter(tags=["Leads ingestion"])


@router.post(
    "/lead",
    response_model=StatusResponse,
    summary="Create lead",
    description=(
        "Accepts a lead from landing traffic, validates affiliate authorization and offer ownership, "
        "then pushes the lead into Redis queue for asynchronous processing by the core service."
    ),
    responses={
        200: {"description": "Lead accepted and queued."},
        401: {"model": ErrorResponse, "description": "Missing/invalid JWT or unknown affiliate."},
        403: {"model": ErrorResponse, "description": "Body affiliate_id does not match token id."},
        404: {"model": ErrorResponse, "description": "Offer is not available for this affiliate."},
        422: {"description": "Validation error for request body fields."},
    },
)
async def create_lead(
    lead: LeadCreate,
    affiliate: Affiliate = Depends(get_current_affiliate),
    db: AsyncSession = Depends(get_db),
) -> StatusResponse:
    if lead.affiliate_id != affiliate.id:
        raise HTTPException(status_code=403, detail="affiliate_id does not match token")

    offer_result = await db.execute(
        select(Offer).where(Offer.id == lead.offer_id, Offer.affiliate_id == lead.affiliate_id)
    )
    offer = offer_result.scalar_one_or_none()
    if offer is None:
        raise HTTPException(status_code=404, detail="offer is not available for affiliate")

    message = LeadQueueMessage(**lead.model_dump()).model_dump_json()
    await enqueue_lead(message)
    return StatusResponse(status="ok")

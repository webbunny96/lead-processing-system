from datetime import datetime

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    affiliate_id: int = Field(gt=0)
    offer_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=5, max_length=50)


class LeadQueueMessage(LeadCreate):
    pass


class LeadAggregation(BaseModel):
    affiliate_id: int
    offer_id: int
    total: int


class LeadOut(BaseModel):
    id: int
    affiliate_id: int
    offer_id: int
    name: str
    phone: str
    created_at: datetime

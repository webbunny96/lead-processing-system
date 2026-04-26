from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    affiliate_id: int = Field(gt=0)
    offer_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=255)
    phone: str = Field(min_length=5, max_length=50)
    country: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")


class LeadQueueMessage(LeadCreate):
    pass


class LeadOut(BaseModel):
    id: int
    affiliate_id: int
    offer_id: int
    name: str
    phone: str
    country: str
    created_at: datetime


class LeadGroupByDate(BaseModel):
    group: Literal["date"] = "date"
    date: date
    count: int
    leads: list[LeadOut]


class LeadGroupByOffer(BaseModel):
    group: Literal["offer"] = "offer"
    offer_id: int
    count: int
    leads: list[LeadOut]

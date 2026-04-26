from datetime import date as dt_date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    affiliate_id: int = Field(
        gt=0,
        description="Affiliate identifier. Must match the id from JWT payload.",
        example=1,
    )
    offer_id: int = Field(
        gt=0,
        description="Offer identifier available to this affiliate.",
        example=1,
    )
    name: str = Field(
        min_length=2,
        max_length=255,
        description="Lead full name.",
        example="Oleksii Shevchenko",
    )
    phone: str = Field(
        min_length=5,
        max_length=50,
        description="Lead contact phone in any accepted business format.",
        example="+380982342123",
    )
    country: str = Field(
        min_length=2,
        max_length=2,
        pattern=r"^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 uppercase country code.",
        example="UA",
    )


class LeadQueueMessage(LeadCreate):
    pass


class LeadOut(BaseModel):
    id: int = Field(description="Persisted lead identifier.", example=42)
    affiliate_id: int = Field(description="Affiliate identifier.", example=1)
    offer_id: int = Field(description="Offer identifier.", example=7)
    name: str = Field(description="Lead full name.", example="Oleksii Shevchenko")
    phone: str = Field(description="Lead phone.", example="+380982342123")
    country: str = Field(description="ISO country code.", example="UA")
    created_at: datetime = Field(
        description="UTC timestamp when the lead was stored.",
        example="2026-04-26T17:15:08.000000",
    )


class LeadGroupByDate(BaseModel):
    group: Literal["date"] = Field(
        default="date",
        description="Aggregation mode marker.",
        example="date",
    )
    date: dt_date = Field(description="Aggregation date.", example="2026-04-26")
    count: int = Field(description="Number of leads in this group.", example=3)
    leads: list[LeadOut] = Field(description="Leads included in the group.")


class LeadGroupByOffer(BaseModel):
    group: Literal["offer"] = Field(
        default="offer",
        description="Aggregation mode marker.",
        example="offer",
    )
    offer_id: int = Field(description="Offer identifier.", example=7)
    count: int = Field(description="Number of leads in this group.", example=5)
    leads: list[LeadOut] = Field(description="Leads included in the group.")


class StatusResponse(BaseModel):
    status: str = Field(description="Operation status.", example="ok")


class ErrorResponse(BaseModel):
    detail: str = Field(description="Error details.", example="Invalid token")

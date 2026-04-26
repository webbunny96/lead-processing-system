from datetime import date as dt_date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    affiliate_id: int = Field(
        gt=0,
        description="Affiliate identifier. Must match the id from JWT payload.",
        json_schema_extra={"example": 1},
    )
    offer_id: int = Field(
        gt=0,
        description="Offer identifier available to this affiliate.",
        json_schema_extra={"example": 1},
    )
    name: str = Field(
        min_length=2,
        max_length=255,
        description="Lead full name.",
        json_schema_extra={"example": "Oleksii Shevchenko"},
    )
    phone: str = Field(
        min_length=5,
        max_length=50,
        description="Lead contact phone in any accepted business format.",
        json_schema_extra={"example": "+380982342123"},
    )
    country: str = Field(
        min_length=2,
        max_length=2,
        pattern=r"^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 uppercase country code.",
        json_schema_extra={"example": "UA"},
    )


class LeadQueueMessage(LeadCreate):
    pass


class LeadOut(BaseModel):
    id: int = Field(description="Persisted lead identifier.", json_schema_extra={"example": 42})
    affiliate_id: int = Field(description="Affiliate identifier.", json_schema_extra={"example": 1})
    offer_id: int = Field(description="Offer identifier.", json_schema_extra={"example": 7})
    name: str = Field(description="Lead full name.", json_schema_extra={"example": "Oleksii Shevchenko"})
    phone: str = Field(description="Lead phone.", json_schema_extra={"example": "+380982342123"})
    country: str = Field(description="ISO country code.", json_schema_extra={"example": "UA"})
    created_at: datetime = Field(
        description="UTC timestamp when the lead was stored.",
        json_schema_extra={"example": "2026-04-26T17:15:08.000000"},
    )


class LeadGroupByDate(BaseModel):
    group: Literal["date"] = Field(
        default="date",
        description="Aggregation mode marker.",
        json_schema_extra={"example": "date"},
    )
    date: dt_date = Field(description="Aggregation date.", json_schema_extra={"example": "2026-04-26"})
    count: int = Field(description="Number of leads in this group.", json_schema_extra={"example": 3})
    leads: list[LeadOut] = Field(description="Leads included in the group.")


class LeadGroupByOffer(BaseModel):
    group: Literal["offer"] = Field(
        default="offer",
        description="Aggregation mode marker.",
        json_schema_extra={"example": "offer"},
    )
    offer_id: int = Field(description="Offer identifier.", json_schema_extra={"example": 7})
    count: int = Field(description="Number of leads in this group.", json_schema_extra={"example": 5})
    leads: list[LeadOut] = Field(description="Leads included in the group.")


class StatusResponse(BaseModel):
    status: str = Field(description="Operation status.", json_schema_extra={"example": "ok"})


class ErrorResponse(BaseModel):
    detail: str = Field(description="Error details.", json_schema_extra={"example": "Invalid token"})

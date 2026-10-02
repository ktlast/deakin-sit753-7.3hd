import os

from fastapi import FastAPI
from pydantic import BaseModel, Field, model_validator

from api.application.utils.calculate_with_items import calculate_balance_summaries
from api.domain.entities.ledger import Item, UserId


class Participant(BaseModel):
    user_id: str = Field(min_length=1)
    weights: float = Field(ge=0, allow_inf_nan=False)
    member_id: str | None = None


class RequestItem(Item):
    @model_validator(mode="before")
    @classmethod
    def validate_participants(cls, values: dict) -> dict:
        values = dict(values)
        for key in ("creditors", "debtors"):
            if key in values:
                values[key] = [
                    Participant.model_validate(entry).model_dump(exclude_none=True)
                    for entry in values[key]
                ]
        return values


class BalanceRequest(BaseModel):
    items: list[RequestItem]
    member_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def check_members(self) -> "BalanceRequest":
        members = set(self.member_ids)
        if "" in members or len(members) != len(self.member_ids):
            raise ValueError("Member IDs must be nonempty and unique")
        for item in self.items:
            for participant in item.creditors + item.debtors:
                if participant["user_id"] not in members:
                    raise ValueError("Every participant must be listed in member_ids")
        return self


app = FastAPI(
    title="Decents Expense Calculation API",
    description="Validate shared expenses and calculate member balances.",
    version="1.0.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": os.getenv("APP_ENV", "local")}


@app.post("/items/validate")
def validate_item(item: RequestItem) -> dict:
    return {"valid": True, "item": item.model_dump(mode="json")}


@app.post("/balances/calculate")
def calculate_balances(request: BalanceRequest) -> dict:
    return {
        "balances": calculate_balance_summaries(
            request.items, [UserId(member) for member in request.member_ids]
        )
    }

from __future__ import annotations

from enum import StrEnum
from typing import NewType, cast

from pydantic import BaseModel, Field, model_validator

from api.domain.value_objects.decimal_amounts import amounts_equal, sum_amounts
from api.domain.value_objects.ledger import Timestamp

ItemId = NewType("ItemId", str)
UserId = NewType("UserId", str)
ItemParticipant = dict[str, float | int | str | None]


class AmountType(StrEnum):
    WEIGHT = "weight"
    AMOUNT = "amount"


class ItemType(StrEnum):
    EXPENSE = "expense"
    TRANSFER = "transfer"


class Item(BaseModel):
    """Domain Entity representing a single item in a ledger."""

    item_id: ItemId
    item_name: str
    ts: Timestamp
    item_type: ItemType = ItemType.EXPENSE
    amount: float = Field(..., ge=0)
    creditors: list[ItemParticipant]
    credit_amount_type: AmountType = AmountType.AMOUNT
    debt_amount_type: AmountType = AmountType.WEIGHT
    debtors: list[ItemParticipant]
    curr: str = Field(..., min_length=3, max_length=3)
    ex_rate: float = Field(..., ge=0)
    desc: str

    def _sum_weights(self, components: list[ItemParticipant]):
        """Helper function to sum weights from a list of components."""
        return sum_amounts([cast(str | int | float, c["weights"]) for c in components])

    def _validate_weights(self, amount_type: AmountType, total, component_type: str) -> None:
        """Helper function to validate weights based on amount type.

        Args:
            amount_type: The type of amount (WEIGHT or AMOUNT)
            total: The sum of weights to validate
            component_type: The type of component being validated ('creditor' or 'debtor')
        """
        match amount_type:
            case AmountType.WEIGHT:
                return  # No validation needed
            case AmountType.AMOUNT:
                if not amounts_equal(self.amount, total):
                    raise ValueError(
                        f"[{component_type}_amount_type = {amount_type}] : "
                        f"Sum of {component_type} weights ({total:.2f}) should be equal to amount ({self.amount})"
                    )

    @model_validator(mode="after")
    def check_transfer_shape(self) -> Item:
        if self.item_type != ItemType.TRANSFER:
            return self
        if len(self.creditors) != 1:
            raise ValueError("Transfer must have exactly one creditor")
        if len(self.debtors) != 1:
            raise ValueError("Transfer must have exactly one debtor")
        if (
            self.credit_amount_type != AmountType.AMOUNT
            or self.debt_amount_type != AmountType.AMOUNT
        ):
            raise ValueError("Transfer credit and debt amount types must both be amount")

        creditor = self.creditors[0]
        debtor = self.debtors[0]
        same_member = creditor.get("member_id") is not None and creditor.get(
            "member_id"
        ) == debtor.get("member_id")
        same_user = creditor.get("user_id") == debtor.get("user_id")
        if same_member or same_user:
            raise ValueError("Transfer creditor and debtor must be distinct")
        return self

    @model_validator(mode="after")
    def check_creditors_weights_correctness(self) -> Item:
        """Validate creditor weights based on credit_amount_type.

        Validation rules:
        - WEIGHT: no validation needed
        - AMOUNT: sum of weights must equal amount
        """
        creditor_sum = self._sum_weights(self.creditors)
        self._validate_weights(self.credit_amount_type, creditor_sum, "creditor")
        return self

    @model_validator(mode="after")
    def check_debtors_weights_correctness(self) -> Item:
        """Validate debtor weights based on debt_amount_type.

        Validation rules:
        - WEIGHT: no validation needed
        - AMOUNT: sum of weights must equal amount
        """
        debtor_sum = self._sum_weights(self.debtors)
        self._validate_weights(self.debt_amount_type, debtor_sum, "debtor")
        return self

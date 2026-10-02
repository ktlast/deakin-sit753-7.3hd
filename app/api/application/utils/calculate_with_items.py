from decimal import ROUND_DOWN, Decimal
from typing import cast

from api.domain.entities.ledger import Item, UserId
from api.domain.value_objects.decimal_amounts import (
    AMOUNT_SCALE,
    amount_to_float,
    quantize_amount,
    to_decimal,
)


def _participant_user_id(entry: dict[str, float | int | str | None]) -> UserId:
    return UserId(str(entry["user_id"]))


def _participant_weight(entry: dict[str, float | int | str | None]) -> Decimal:
    return quantize_amount(cast(str | int | float, entry["weights"]))


def _split_amount_by_values(
    entries: list[dict[str, float | int | str | None]],
    total_amount: Decimal,
) -> list[tuple[UserId, Decimal]]:
    values = [
        (_participant_user_id(entry), _participant_weight(entry))
        for entry in entries
    ]
    total_value = sum((value for _, value in values), quantize_amount(0))
    if total_value <= 0:
        return [(user_id, quantize_amount(0)) for user_id, _ in values]

    raw_amounts = [
        (user_id, (value / total_value) * total_amount)
        for user_id, value in values
    ]
    allocated_amounts = [
        (user_id, amount.quantize(AMOUNT_SCALE, rounding=ROUND_DOWN))
        for user_id, amount in raw_amounts
    ]
    remainder = quantize_amount(
        total_amount - sum((amount for _, amount in allocated_amounts), quantize_amount(0))
    )

    result = []
    for index, (user_id, amount) in enumerate(allocated_amounts):
        amount_with_remainder = amount + (remainder if index == 0 else 0)
        result.append((user_id, quantize_amount(amount_with_remainder)))
    return result


def calculate_balance_summaries(
    ledger_items: list[Item], member_ids: list[UserId]
) -> list[dict[str, dict[str, float]]]:
    finance_summary = {
        user_id: {"total_credits": quantize_amount(0), "total_debts": quantize_amount(0)}
        for user_id in member_ids
    }

    for item in ledger_items:
        item_amount = quantize_amount(item.amount)
        item_ex_rate = to_decimal(item.ex_rate)
        item_total = quantize_amount(item_amount * item_ex_rate)
        # Calculate credits
        if item.creditors:
            for user_id, credit_amount in _split_amount_by_values(item.creditors, item_total):
                if user_id in finance_summary:
                    finance_summary[user_id]["total_credits"] = quantize_amount(
                        finance_summary[user_id]["total_credits"] + credit_amount
                    )

        # Calculate debts
        if item.debtors:
            for user_id, debt_amount in _split_amount_by_values(item.debtors, item_total):
                if user_id in finance_summary:
                    finance_summary[user_id]["total_debts"] = quantize_amount(
                        finance_summary[user_id]["total_debts"] + debt_amount
                    )

    result = []
    for user_id, finances in finance_summary.items():
        # 應付款就是總債務 - 總已付；如果應付款為負，表示應收
        net_pay = quantize_amount(finances["total_debts"] - finances["total_credits"])
        result.append(
            {
                str(user_id): {
                    "total_credits": amount_to_float(finances["total_credits"]),
                    "total_debts": amount_to_float(finances["total_debts"]),
                    "net_pay": amount_to_float(net_pay),
                }
            }
        )
    return result

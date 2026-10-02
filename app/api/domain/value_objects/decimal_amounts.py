from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

AMOUNT_SCALE = Decimal("0.000001")
EX_RATE_SCALE = Decimal("0.00000001")


def to_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def quantize_amount(value: Any) -> Decimal:
    return to_decimal(value).quantize(AMOUNT_SCALE, rounding=ROUND_HALF_UP)


def quantize_ex_rate(value: Any) -> Decimal:
    return to_decimal(value).quantize(EX_RATE_SCALE, rounding=ROUND_HALF_UP)


def sum_amounts(values: list[Any]) -> Decimal:
    return quantize_amount(sum((to_decimal(value) for value in values), Decimal("0")))


def amounts_equal(left: Any, right: Any) -> bool:
    return quantize_amount(left) == quantize_amount(right)


def amount_to_float(value: Any) -> float:
    return float(quantize_amount(value))

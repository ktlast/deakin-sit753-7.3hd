import pytest

from api.application.utils.calculate_with_items import calculate_balance_summaries
from api.domain.entities.ledger import AmountType, Item, ItemId, ItemType, UserId
from api.domain.value_objects.ledger import Timestamp


@pytest.mark.unittest
def test_calculate_balance_summaries_quantizes_binary_float_artifacts():
    item = Item(
        amount=0.3,
        debtors=[
            {"user_id": "debtor", "weights": 0.1 + 0.2},
        ],
        item_name="foo",
        creditors=[{"user_id": "creditor", "weights": 0.3}],
        curr="TWD",
        ex_rate=1,
        debt_amount_type=AmountType.AMOUNT,
        item_id=ItemId("foo"),
        ts=Timestamp(1234567890),
        desc="foo",
    )

    result = calculate_balance_summaries(
        [item],
        [UserId("creditor"), UserId("debtor")],
    )

    assert result == [
        {"creditor": {"total_credits": 0.3, "total_debts": 0.0, "net_pay": -0.3}},
        {"debtor": {"total_credits": 0.0, "total_debts": 0.3, "net_pay": 0.3}},
    ]


@pytest.mark.unittest
def test_calculate_balance_summaries_quantizes_weight_splits():
    item = Item(
        amount=1,
        debtors=[
            {"user_id": "a", "weights": 1},
            {"user_id": "b", "weights": 2},
        ],
        item_name="foo",
        creditors=[{"user_id": "payer", "weights": 1}],
        curr="TWD",
        ex_rate=1,
        debt_amount_type=AmountType.WEIGHT,
        item_id=ItemId("foo"),
        ts=Timestamp(1234567890),
        desc="foo",
    )

    result = calculate_balance_summaries(
        [item],
        [UserId("payer"), UserId("a"), UserId("b")],
    )

    assert result == [
        {"payer": {"total_credits": 1.0, "total_debts": 0.0, "net_pay": -1.0}},
        {"a": {"total_credits": 0.0, "total_debts": 0.333334, "net_pay": 0.333334}},
        {"b": {"total_credits": 0.0, "total_debts": 0.666666, "net_pay": 0.666666}},
    ]


@pytest.mark.unittest
def test_calculate_balance_summaries_preserves_item_total_after_rounding():
    item = Item(
        amount=1,
        debtors=[
            {"user_id": "a", "weights": 1},
            {"user_id": "b", "weights": 1},
            {"user_id": "c", "weights": 1},
        ],
        item_name="foo",
        creditors=[{"user_id": "payer", "weights": 1}],
        curr="TWD",
        ex_rate=1,
        debt_amount_type=AmountType.WEIGHT,
        item_id=ItemId("foo"),
        ts=Timestamp(1234567890),
        desc="foo",
    )

    result = calculate_balance_summaries(
        [item],
        [UserId("payer"), UserId("a"), UserId("b"), UserId("c")],
    )

    total_net_pay = sum(next(iter(entry.values()))["net_pay"] for entry in result)

    assert total_net_pay == 0


@pytest.mark.unittest
def test_calculate_balance_summaries_includes_transfer_items() -> None:
    item = Item(
        item_type=ItemType.TRANSFER,
        amount=100,
        debtors=[{"user_id": "recipient", "member_id": "m2", "weights": 100}],
        item_name="bank transfer",
        creditors=[{"user_id": "sender", "member_id": "m1", "weights": 100}],
        credit_amount_type=AmountType.AMOUNT,
        debt_amount_type=AmountType.AMOUNT,
        curr="USD",
        ex_rate=1,
        item_id=ItemId("transfer"),
        ts=Timestamp(1234567890),
        desc="",
    )

    result = calculate_balance_summaries(
        [item],
        [UserId("sender"), UserId("recipient")],
    )

    assert result == [
        {"sender": {"total_credits": 100.0, "total_debts": 0.0, "net_pay": -100.0}},
        {
            "recipient": {
                "total_credits": 0.0,
                "total_debts": 100.0,
                "net_pay": 100.0,
            }
        },
    ]


@pytest.mark.unittest
def test_calculate_balance_summaries_combines_expense_and_converted_transfer() -> None:
    expense = Item(
        amount=100,
        debtors=[
            {"user_id": "sender", "weights": 50},
            {"user_id": "recipient", "weights": 50},
        ],
        item_name="dinner",
        creditors=[{"user_id": "sender", "weights": 100}],
        debt_amount_type=AmountType.AMOUNT,
        curr="TWD",
        ex_rate=1,
        item_id=ItemId("expense"),
        ts=Timestamp(1234567890),
        desc="",
    )
    transfer = Item(
        item_type=ItemType.TRANSFER,
        amount=30,
        debtors=[{"user_id": "recipient", "weights": 30}],
        item_name="converted transfer",
        creditors=[{"user_id": "sender", "weights": 30}],
        credit_amount_type=AmountType.AMOUNT,
        debt_amount_type=AmountType.AMOUNT,
        curr="USD",
        ex_rate=2,
        item_id=ItemId("transfer"),
        ts=Timestamp(1234567890),
        desc="",
    )

    result = calculate_balance_summaries(
        [expense, transfer],
        [UserId("sender"), UserId("recipient")],
    )

    assert result == [
        {
            "sender": {
                "total_credits": 160.0,
                "total_debts": 50.0,
                "net_pay": -110.0,
            }
        },
        {
            "recipient": {
                "total_credits": 0.0,
                "total_debts": 110.0,
                "net_pay": 110.0,
            }
        },
    ]
    assert sum(next(iter(entry.values()))["net_pay"] for entry in result) == 0

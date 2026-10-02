from typing import cast

import pytest

from api.domain.entities.ledger import AmountType, Item, ItemId, ItemType
from api.domain.value_objects.ledger import Timestamp

USER_ID_FOR_TEST = "foo.bar"



@pytest.mark.unittest
class TestItemWeights:
    @staticmethod
    def test_weight():
        Item(
            amount=1000,
            debtors=[
                {"user_id": "foo1", "weights": 1},
                {"user_id": "foo2", "weights": 2},
            ],
            item_name="foo",
            creditors=[{"user_id": USER_ID_FOR_TEST, "weights": 1000}],
            curr="TWD",
            ex_rate=1,
            debt_amount_type=AmountType.WEIGHT,
            item_id=ItemId("foo"),
            ts=Timestamp(1234567890),
            desc="foo",
        )

    @staticmethod
    def test_amount():
        Item(
            amount=1000,
            debtors=[
                {"user_id": "foo1", "weights": 600},
                {"user_id": "foo2", "weights": 400},
            ],
            item_name="foo",
            creditors=[{"user_id": USER_ID_FOR_TEST, "weights": 1000}],
            curr="TWD",
            ex_rate=1,
            debt_amount_type=AmountType.AMOUNT,
            item_id=ItemId("foo"),
            ts=Timestamp(1234567890),
            desc="foo",
        )

        with pytest.raises(ValueError):
            Item(
                amount=1000,
                debtors=[
                    {"user_id": "foo1", "weights": 500},
                    {"user_id": "foo2", "weights": 400},
                ],
                item_name="foo",
                creditors=[{"user_id": USER_ID_FOR_TEST, "weights": 1000}],
                curr="TWD",
                ex_rate=1,
                debt_amount_type=AmountType.AMOUNT,
                item_id=ItemId("foo"),
                ts=Timestamp(1234567890),
                desc="foo",
            )

    @staticmethod
    def test_amount_accepts_binary_float_artifacts_at_supported_precision():
        Item(
            amount=0.3,
            debtors=[
                {"user_id": "foo1", "weights": 0.1 + 0.2},
            ],
            item_name="foo",
            creditors=[{"user_id": USER_ID_FOR_TEST, "weights": 0.3}],
            curr="TWD",
            ex_rate=1,
            debt_amount_type=AmountType.AMOUNT,
            item_id=ItemId("foo"),
            ts=Timestamp(1234567890),
            desc="foo",
        )

    @staticmethod
    def test_amount_rejects_mismatch_inside_old_error_margin():
        with pytest.raises(ValueError):
            Item(
                amount=1,
                debtors=[
                    {"user_id": "foo1", "weights": 0.995},
                ],
                item_name="foo",
                creditors=[{"user_id": USER_ID_FOR_TEST, "weights": 1}],
                curr="TWD",
                ex_rate=1,
                debt_amount_type=AmountType.AMOUNT,
                item_id=ItemId("foo"),
                ts=Timestamp(1234567890),
                desc="foo",
            )

    @staticmethod
    def test_percent_is_not_supported():
        with pytest.raises(ValueError):
            Item(
                amount=1000,
                debtors=[
                    {"user_id": "foo1", "weights": 3333},
                    {"user_id": "foo2", "weights": 6666},
                ],
                item_name="foo",
                creditors=[{"user_id": USER_ID_FOR_TEST, "weights": 1000}],
                curr="TWD",
                ex_rate=1,
                debt_amount_type=cast(AmountType, "percent"),
                item_id=ItemId("foo"),
                ts=Timestamp(1234567890),
                desc="foo",
            )


def _transfer_item(**overrides) -> Item:
    omit_item_type = overrides.pop("omit_item_type", False)
    values = {
        "item_type": ItemType.TRANSFER,
        "amount": 100,
        "debtors": [{"user_id": "debtor", "member_id": "m2", "weights": 100}],
        "item_name": "transfer",
        "creditors": [{"user_id": "creditor", "member_id": "m1", "weights": 100}],
        "credit_amount_type": AmountType.AMOUNT,
        "debt_amount_type": AmountType.AMOUNT,
        "curr": "USD",
        "ex_rate": 1,
        "item_id": ItemId("transfer"),
        "ts": Timestamp(1234567890),
        "desc": "",
    }
    values.update(overrides)
    if omit_item_type:
        values.pop("item_type")
    return Item(**values)


@pytest.mark.unittest
def test_item_defaults_to_expense_and_serializes_item_type() -> None:
    item = _transfer_item(omit_item_type=True)

    assert item.item_type == ItemType.EXPENSE
    assert item.model_dump(mode="json")["item_type"] == "expense"


@pytest.mark.unittest
def test_transfer_accepts_one_distinct_creditor_and_debtor() -> None:
    item = _transfer_item()

    assert item.item_type == ItemType.TRANSFER
    assert item.amount == 100


@pytest.mark.unittest
def test_transfer_accepts_zero_amount_placeholder() -> None:
    item = _transfer_item(
        amount=0,
        creditors=[{"user_id": "creditor", "member_id": "m1", "weights": 0}],
        debtors=[{"user_id": "debtor", "member_id": "m2", "weights": 0}],
    )

    assert item.amount == 0


@pytest.mark.unittest
@pytest.mark.parametrize(
    ("override", "error"),
    [
        ({"creditors": []}, "exactly one creditor"),
        (
            {
                "debtors": [
                    {"user_id": "debtor", "member_id": "m2", "weights": 50},
                    {"user_id": "other", "member_id": "m3", "weights": 50},
                ]
            },
            "exactly one debtor",
        ),
        (
            {"debtors": [{"user_id": "creditor", "member_id": "m1", "weights": 100}]},
            "must be distinct",
        ),
        (
            {"debtors": [{"user_id": "creditor", "member_id": "m2", "weights": 100}]},
            "must be distinct",
        ),
        ({"debt_amount_type": AmountType.WEIGHT}, "amount types"),
    ],
)
def test_transfer_rejects_invalid_participant_shape(override, error) -> None:
    with pytest.raises(ValueError, match=error):
        _transfer_item(**override)

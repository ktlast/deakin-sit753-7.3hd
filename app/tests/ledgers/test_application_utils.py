import pytest

from api.application.utils.calculate_with_items import calculate_balance_summaries
from api.domain.entities.ledger import (
    Item,
    UserId,
)
from tests.ledgers.data import STANDARD_ITEM_1, STANDARD_ITEM_2


def results_to_dict(
    results_list: list[dict[str, dict[str, float]]],
) -> dict[str, dict[str, float]]:
    """Converts the list of results into a dictionary keyed by member ID."""
    return {list(d.keys())[0]: list(d.values())[0] for d in results_list}


@pytest.mark.parametrize(
    "ledger_items_data, member_ids, expected_balances_dict",
    [
        (
            STANDARD_ITEM_1,
            [
                "@foo.bar",
                "s.user.1",
                "s.user.2",
                "s.user.3",
                "@foo.tim",
            ],  # member_ids
            {  # expected_balances_dict
                "@foo.bar": {
                    "total_credits": 1021.0,
                    "total_debts": 318.10,
                    "net_pay": -702.90,
                },
                "s.user.1": {
                    "total_credits": 177.0,
                    "total_debts": 373.60,
                    "net_pay": 196.60,
                },
                "s.user.2": {
                    "total_credits": 44.0,
                    "total_debts": 373.60,
                    "net_pay": 329.60,
                },
                "s.user.3": {
                    "total_credits": 0.0,
                    "total_debts": 487.60,
                    "net_pay": 487.60,
                },
                "@foo.tim": {
                    "total_credits": 666.0,
                    "total_debts": 355.10,
                    "net_pay": -310.90,
                },
            },
        ),
        (
            STANDARD_ITEM_2,
            [
                "@foo.bar",
                "s.user.1",
                "s.user.2",
                "s.user.3",
                "@foo.tim",
            ],
            {
                "@foo.bar": {
                    "total_credits": 3630.68,
                    "total_debts": 789.5,
                    "net_pay": -2841.18,
                },
                "s.user.1": {
                    "total_credits": 537.38,
                    "total_debts": 1947.605,
                    "net_pay": 1410.225,
                },
                "@foo.tim": {
                    "total_credits": 1794.0,
                    "total_debts": 1330.515,
                    "net_pay": -463.485,
                },
                "s.user.2": {
                    "total_credits": 0.0,
                    "total_debts": 2246.605,
                    "net_pay": 2246.605,
                },
                "s.user.3": {
                    "total_credits": 2299.77,
                    "total_debts": 1947.605,
                    "net_pay": -352.165,
                },
            },
        ),
    ],
)
def test_calculate_balance_summaries(
    ledger_items_data, member_ids, expected_balances_dict
):
    typed_members = [UserId(p_id) for p_id in member_ids]

    ledger_items = [Item(**data) for data in ledger_items_data]

    actual_results_list = calculate_balance_summaries(ledger_items, typed_members)
    actual_results_dict = results_to_dict(actual_results_list)

    assert len(actual_results_dict) == len(expected_balances_dict)

    for member_id, expected_data in expected_balances_dict.items():
        print(f"member_id: {member_id}")
        assert (
            member_id in actual_results_dict
        ), f"Member {member_id} not found in results"

        actual_data = actual_results_dict[member_id]
        assert actual_data["total_credits"] == pytest.approx(
            expected_data["total_credits"]
        )
        assert actual_data["total_debts"] == pytest.approx(expected_data["total_debts"])
        assert actual_data["net_pay"] == pytest.approx(expected_data["net_pay"])

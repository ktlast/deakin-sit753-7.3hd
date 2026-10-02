import json
import os
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(params=["in_process", "deployed"])
def client(request):
    if request.param == "in_process":
        with TestClient(app) as test_client:
            yield test_client
    else:
        with httpx.Client(base_url=os.environ["TEST_API_URL"], timeout=10) as test_client:
            yield test_client


@pytest.fixture
def item():
    path = Path(__file__).resolve().parents[2] / "examples/item.json"
    return json.loads(path.read_text())


def test_health_and_docs(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "environment": "ci"}
    assert client.get("/docs").status_code == 200


def test_valid_expense(client, item):
    response = client.post("/items/validate", json=item)
    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert response.json()["item"]["item_type"] == "expense"


def test_equal_split(client, item):
    response = client.post(
        "/balances/calculate", json={"items": [item], "member_ids": ["alice", "bob"]}
    )
    assert response.status_code == 200
    assert response.json()["balances"] == [
        {"alice": {"total_credits": 120.0, "total_debts": 60.0, "net_pay": -60.0}},
        {"bob": {"total_credits": 0.0, "total_debts": 60.0, "net_pay": 60.0}},
    ]


def test_weighted_split_with_conversion(client, item):
    item["debtors"][1]["weights"] = 2
    item["ex_rate"] = 2
    response = client.post(
        "/balances/calculate", json={"items": [item], "member_ids": ["alice", "bob"]}
    )
    assert response.status_code == 200
    balances = response.json()["balances"]
    assert balances[0]["alice"]["net_pay"] == -160.0
    assert balances[1]["bob"]["net_pay"] == 160.0


def test_transfer(client, item):
    item.update({
        "item_type": "transfer",
        "debt_amount_type": "amount",
        "debtors": [{"user_id": "bob", "weights": 120}],
    })
    response = client.post(
        "/balances/calculate", json={"items": [item], "member_ids": ["alice", "bob"]}
    )
    assert response.status_code == 200
    balances = response.json()["balances"]
    assert balances[0]["alice"]["net_pay"] == -120.0
    assert balances[1]["bob"]["net_pay"] == 120.0


@pytest.mark.parametrize("invalid", [
    {"amount": -1},
    {"creditors": [{"user_id": "alice", "weights": 100}]},
    {"debtors": [{"weights": 1}]},
    {"debtors": [{"user_id": "bob", "weights": -1}]},
    {"item_type": "transfer", "debt_amount_type": "amount",
     "debtors": [{"user_id": "alice", "weights": 120}]},
])
def test_invalid_item_returns_422(client, item, invalid):
    item.update(invalid)
    assert client.post("/items/validate", json=item).status_code == 422


@pytest.mark.parametrize("members", [["alice"], ["alice", "alice"], [""]])
def test_invalid_member_list_returns_422(client, item, members):
    response = client.post("/balances/calculate", json={"items": [item], "member_ids": members})
    assert response.status_code == 422


def test_empty_ledger_returns_zero_balances(client):
    response = client.post("/balances/calculate", json={"items": [], "member_ids": ["alice"]})
    assert response.status_code == 200
    assert response.json()["balances"] == [
        {"alice": {"total_credits": 0.0, "total_debts": 0.0, "net_pay": 0.0}}
    ]

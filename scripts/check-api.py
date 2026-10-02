import json
import sys
import urllib.request

base = "http://127.0.0.1:8080"
with urllib.request.urlopen(base + "/health", timeout=5) as response:
    health = json.load(response)
if health != {"status": "ok", "environment": sys.argv[1]}:
    raise SystemExit("Unexpected health response")
item = {
    "item_id": "dinner", "item_name": "Shared dinner", "ts": 1742108367,
    "amount": 120, "creditors": [{"user_id": "alice", "weights": 120}],
    "debtors": [{"user_id": "alice", "weights": 1}, {"user_id": "bob", "weights": 1}],
    "curr": "AUD", "ex_rate": 1, "desc": "Shared dinner",
}
request = urllib.request.Request(
    base + "/balances/calculate",
    data=json.dumps({"items": [item], "member_ids": ["alice", "bob"]}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=5) as response:
    result = json.load(response)
expected = [
    {"alice": {"total_credits": 120.0, "total_debts": 60.0, "net_pay": -60.0}},
    {"bob": {"total_credits": 0.0, "total_debts": 60.0, "net_pay": 60.0}},
]
if result.get("balances") != expected:
    raise SystemExit("Unexpected balance calculation")
print(json.dumps({"health": health, "calculation": result}, indent=2))

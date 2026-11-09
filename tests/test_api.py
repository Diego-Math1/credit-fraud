# tests/test_api.py
import pytest
from fastapi.testclient import TestClient

from src.serving.main import app


@pytest.fixture(scope="module")
def client():
    """Sobe a app com lifespan — modelo é carregado no startup."""
    with TestClient(app) as c:
        yield c


VALID_TRANSACTION = {
    "amount": 68.5,
    "txn_count_1h": 2,
    "amount_sum_1h": 120.0,
    "amount_avg_1h": 60.0,
    "txn_count_24h": 5,
    "amount_sum_24h": 350.0,
    "amount_avg_24h": 70.0,
    "txn_count_7d": 12,
    "amount_sum_7d": 900.0,
    "amount_avg_7d": 75.0,
    "amount_avg_last30": 65.0,
    "amount_std_last30": 25.0,
    "amount_deviation_ratio": 1.05,
    "amount_zscore_last30": 0.14,
    "seconds_since_prev_txn": 3600.0,
    "product_code": "W",
    "purchaser_email_domain": "gmail.com",
    "recipient_email_domain": None,
}


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert data["model_version"] is not None


def test_predict_returns_valid_response(client):
    r = client.post("/predict", json=VALID_TRANSACTION)
    assert r.status_code == 200
    data = r.json()
    assert 0.0 <= data["probability"] <= 1.0
    assert data["decision"] in {"approve", "review", "block"}
    assert data["model_version"] is not None


def test_predict_rejects_negative_amount(client):
    bad = {**VALID_TRANSACTION, "amount": -10.0}
    r = client.post("/predict", json=bad)
    assert r.status_code == 422


def test_predict_rejects_missing_required_field(client):
    bad = {k: v for k, v in VALID_TRANSACTION.items() if k != "amount"}
    r = client.post("/predict", json=bad)
    assert r.status_code == 422


def test_predict_handles_missing_optional(client):
    minimal = {
        "amount": 50.0,
        "txn_count_1h": 0,
        "amount_sum_1h": 0.0,
        "txn_count_24h": 0,
        "amount_sum_24h": 0.0,
        "txn_count_7d": 0,
        "amount_sum_7d": 0.0,
        "product_code": "W",
    }
    r = client.post("/predict", json=minimal)
    assert r.status_code == 200


def test_predict_decision_thresholds(client):
    """Testa se decision respeita os thresholds configurados."""
    r = client.post("/predict", json=VALID_TRANSACTION)
    proba = r.json()["probability"]
    decision = r.json()["decision"]
    if proba >= 0.8:
        assert decision == "block"
    elif proba >= 0.5:
        assert decision == "review"
    else:
        assert decision == "approve"

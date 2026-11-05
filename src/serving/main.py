# src/serving/main.py (placeholder — Fase 1)
from fastapi import FastAPI

app = FastAPI(title="Credit Fraud Scoring API")


@app.get("/health")
def health():
    return {"status": "ok", "service": "credit-fraud-api"}

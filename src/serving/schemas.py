# src/serving/schemas.py
from typing import Literal

from pydantic import BaseModel, Field


class TransactionFeatures(BaseModel):
    """Features de uma única transação para predição de fraude."""

    # Numéricas
    amount: float = Field(..., ge=0, description="Valor da transação")
    txn_count_1h: int = Field(..., ge=0)
    amount_sum_1h: float = Field(..., ge=0)
    amount_avg_1h: float | None = None
    txn_count_24h: int = Field(..., ge=0)
    amount_sum_24h: float = Field(..., ge=0)
    amount_avg_24h: float | None = None
    txn_count_7d: int = Field(..., ge=0)
    amount_sum_7d: float = Field(..., ge=0)
    amount_avg_7d: float | None = None
    amount_avg_last30: float | None = None
    amount_std_last30: float | None = None
    amount_deviation_ratio: float | None = None
    amount_zscore_last30: float | None = None
    seconds_since_prev_txn: float | None = None

    # Categóricas
    product_code: str = Field(..., description="ProductCD (ex: W, H, C, S, R)")
    purchaser_email_domain: str | None = None
    recipient_email_domain: str | None = None


class PredictionResponse(BaseModel):
    transaction_id: str | None = None
    probability: float = Field(..., ge=0, le=1, description="Probabilidade calibrada de fraude")
    decision: Literal["approve", "review", "block"]
    model_version: str


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    model_loaded: bool
    model_version: str | None

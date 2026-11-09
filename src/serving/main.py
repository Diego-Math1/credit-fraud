# src/serving/main.py
import logging
import os
from contextlib import asynccontextmanager

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from .model_loader import ModelBundle, load_model_bundle
from .schemas import HealthResponse, PredictionResponse, TransactionFeatures

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thresholds configuráveis por env
BLOCK_THRESHOLD = float(os.getenv("BLOCK_THRESHOLD", "0.8"))
REVIEW_THRESHOLD = float(os.getenv("REVIEW_THRESHOLD", "0.5"))

# Estado global (populado no startup)
_state: dict = {"bundle": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carrega o modelo no startup, libera no shutdown."""
    logger.info("Carregando modelo...")
    try:
        _state["bundle"] = load_model_bundle()
        logger.info(f"✅ Modelo {_state['bundle'].version} carregado")
    except Exception as e:
        logger.error(f"❌ Falha ao carregar modelo: {e}")
        _state["bundle"] = None
    yield
    logger.info("Encerrando API")
    _state["bundle"] = None


app = FastAPI(
    title="Credit Fraud Scoring API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health():
    bundle = _state["bundle"]
    if bundle is None:
        return HealthResponse(status="degraded", model_loaded=False, model_version=None)
    return HealthResponse(status="ok", model_loaded=True, model_version=bundle.version)


@app.post("/predict", response_model=PredictionResponse)
def predict(transaction: TransactionFeatures):
    bundle: ModelBundle | None = _state["bundle"]
    if bundle is None:
        raise HTTPException(status_code=503, detail="Modelo não carregado")

    # 1. Converte Pydantic → DataFrame
    df = pd.DataFrame([transaction.model_dump()])

    # 2. Aplica preprocessor (mesmo do treino)
    try:
        X_encoded = bundle.preprocessor.transform(df)
    except Exception as e:
        logger.error(f"Erro no preprocessor: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no preprocessor: {e}") from None

    # 3. Predição calibrada
    try:
        proba = float(bundle.model.predict_proba(X_encoded)[0, 1])
    except Exception as e:
        logger.error(f"Erro na predição: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na predição: {e}") from None

    # 4. Decision logic
    if proba >= BLOCK_THRESHOLD:
        decision = "block"
    elif proba >= REVIEW_THRESHOLD:
        decision = "review"
    else:
        decision = "approve"

    return PredictionResponse(
        probability=proba,
        decision=decision,
        model_version=bundle.version,
    )

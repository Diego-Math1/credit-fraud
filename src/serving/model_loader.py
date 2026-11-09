# src/serving/model_loader.py
import logging
import os
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn

logger = logging.getLogger(__name__)

MODEL_NAME = os.getenv("MODEL_NAME", "fraud_scoring_xgb")
MODEL_STAGE = os.getenv("MODEL_STAGE", "latest")
PREPROCESSOR_PATH = os.getenv("PREPROCESSOR_PATH", "/app/preprocessor.joblib")


class ModelBundle:
    def __init__(self, model, preprocessor, version: str):
        self.model = model
        self.preprocessor = preprocessor
        self.version = version


def _find_model_artifact_dir() -> tuple[str, str] | None:
    """
    Localiza o diretório de artefatos do modelo mais recente dentro de mlruns.
    Retorna (caminho_do_modelo, version) ou None.

    Isso evita depender do MLflow Registry, cujo meta.yaml pode conter
    paths absolutos incompatíveis entre Windows (host) e Linux (container).
    """
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:///app/mlruns")
    base = tracking_uri.replace("file://", "").replace("file:", "")
    base_path = Path(base)

    if not base_path.exists():
        logger.warning(f"Diretório mlruns não encontrado: {base_path}")
        return None

    # Procura experiment_id/run_id/artifacts/model/MLmodel
    candidates = list(base_path.glob("*/[0-9a-f][0-9a-f]*/artifacts/model/MLmodel"))
    if not candidates:
        logger.warning(f"Nenhum artifacts/model encontrado em {base_path}")
        return None

    # Pega o mais recente
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    model_dir = candidates[0].parent
    version = "latest"

    logger.info(f"Model artifact encontrado: {model_dir}")
    return str(model_dir), version


def load_model_bundle() -> ModelBundle:
    # 1. Configura MLflow
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:///app/mlruns")
    mlflow.set_tracking_uri(tracking_uri)
    logger.info(f"MLflow tracking URI: {tracking_uri}")

    # 2. Carrega preprocessor
    preproc_path = Path(PREPROCESSOR_PATH)
    if not preproc_path.exists():
        raise FileNotFoundError(f"Preprocessor não encontrado: {preproc_path}")
    preprocessor = joblib.load(preproc_path)
    logger.info(f"Preprocessor carregado: {preproc_path}")

    # 3. Carrega modelo — tenta caminho direto primeiro, Registry como fallback
    found = _find_model_artifact_dir()
    if found:
        model_dir, version = found
        logger.info(f"Carregando modelo de: {model_dir}")
        model = mlflow.sklearn.load_model(model_dir)
    else:
        model_uri = f"models:/{MODEL_NAME}/{MODEL_STAGE}"
        logger.info(f"Fallback para Registry: {model_uri}")
        model = mlflow.sklearn.load_model(model_uri)
        version = MODEL_STAGE

    logger.info(f"Modelo carregado (version={version})")
    return ModelBundle(model=model, preprocessor=preprocessor, version=version)

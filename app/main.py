"""Ponto de entrada da aplicação FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, health, predict
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.ml.model import IrisModel
from app.observability.metrics import setup_metrics
from app.observability.middleware import RequestContextLogMiddleware

settings = get_settings()
setup_logging(level=settings.log_level, json_format=settings.log_json)
logger = logging.getLogger("iris_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    model = IrisModel(model_path=settings.model_path, classes_path=settings.classes_path)
    model.load()
    app.state.model = model
    logger.info("aplicacao_iniciada", extra={"modelo_carregado": model.is_loaded})
    yield
    logger.info("aplicacao_finalizada")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "API para classificação de espécies de Iris com base em medidas de "
            "sépalas e pétalas. Inclui autenticação JWT (mockada), predição em "
            "lote e observabilidade (logs estruturados + métricas Prometheus)."
        ),
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextLogMiddleware)

    if settings.metrics_enabled:
        setup_metrics(app)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(predict.router)

    return app


app = create_app()

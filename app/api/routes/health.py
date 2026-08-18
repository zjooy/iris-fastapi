"""Rotas de saúde e informações gerais da API (não exigem autenticação)."""

from fastapi import APIRouter, Depends

from app.api.deps import get_model
from app.core.config import Settings, get_settings
from app.ml.model import IrisModel
from app.models.schemas import HealthResponse

router = APIRouter(tags=["Status"])


@router.get("/", summary="Informações gerais da API")
def home(settings: Settings = Depends(get_settings), model: IrisModel = Depends(get_model)) -> dict:
    return {
        "nome": settings.app_name,
        "versao": settings.app_version,
        "descricao": "Classifica espécies de Iris com base em medidas de sépalas e pétalas.",
        "endpoints": {
            "GET /": "Informações gerais da API",
            "GET /health": "Status da API e do carregamento do modelo",
            "GET /docs": "Documentação interativa (Swagger UI)",
            "POST /auth/login": "Autenticação (usuário mockado) e emissão de JWT",
            "POST /predict": "Predição individual (requer Bearer token)",
            "POST /predict/batch": "Predição em lote (requer Bearer token)",
            "GET /metrics": "Métricas Prometheus",
        },
        "modelo_carregado": model.is_loaded,
    }


@router.get("/health", response_model=HealthResponse, summary="Verifica a saúde da API")
def health(
    settings: Settings = Depends(get_settings), model: IrisModel = Depends(get_model)
) -> HealthResponse:
    return HealthResponse(
        status="healthy" if model.is_loaded else "unhealthy",
        modelo_carregado=model.is_loaded,
        versao=settings.app_version,
    )

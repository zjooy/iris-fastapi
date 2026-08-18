"""Modelos Pydantic (contratos de entrada/saída da API)."""

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings

_settings = get_settings()


class IrisRequest(BaseModel):
    """Dados que o cliente deve enviar para /predict."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            }
        }
    )

    sepal_length: float = Field(..., gt=0, description="Comprimento da sépala em cm")
    sepal_width: float = Field(..., gt=0, description="Largura da sépala em cm")
    petal_length: float = Field(..., gt=0, description="Comprimento da pétala em cm")
    petal_width: float = Field(..., gt=0, description="Largura da pétala em cm")


class IrisPrediction(BaseModel):
    """Espécie prevista pelo modelo."""

    classe: str = Field(..., description="Nome da espécie prevista pelo modelo")
    classe_idx: int = Field(..., description="Índice numérico da espécie prevista pelo modelo")


class IrisProbability(BaseModel):
    """Probabilidade por classe."""

    setosa: float = Field(..., description="Probabilidade da espécie Iris-setosa")
    versicolor: float = Field(..., description="Probabilidade da espécie Iris-versicolor")
    virginica: float = Field(..., description="Probabilidade da espécie Iris-virginica")


class IrisResponse(BaseModel):
    """Resposta de uma predição individual."""

    sucesso: bool = Field(..., description="Indica se a predição foi realizada com sucesso")
    prediction: IrisPrediction = Field(..., description="Predição do modelo")
    probability: IrisProbability = Field(..., description="Probabilidade por classe")
    entrada_recebida: IrisRequest = Field(..., description="Dados de entrada recebidos para a predição")


class IrisBatchRequest(BaseModel):
    """Lote de amostras para predição em /predict/batch."""

    items: list[IrisRequest] = Field(
        ...,
        min_length=1,
        max_length=_settings.batch_max_items,
        description=f"Lista de amostras a classificar (máximo {_settings.batch_max_items} por requisição)",
    )


class IrisBatchResponse(BaseModel):
    """Resposta de um lote de predições."""

    sucesso: bool = Field(..., description="Indica se o lote foi processado com sucesso")
    total: int = Field(..., description="Quantidade de amostras processadas")
    resultados: list[IrisResponse] = Field(..., description="Resultado de cada amostra, na ordem enviada")


class HealthResponse(BaseModel):
    status: str = Field(..., description="'healthy' ou 'unhealthy'")
    modelo_carregado: bool = Field(..., description="Se o modelo de ML foi carregado com sucesso")
    versao: str = Field(..., description="Versão da API")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Tempo de expiração do token em segundos")

"""Rotas de predição (individual e em lote). Ambas exigem Bearer token."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_model
from app.core.security import get_current_user
from app.ml.model import IrisModel, ModelNotLoadedError
from app.models.schemas import IrisBatchRequest, IrisBatchResponse, IrisRequest, IrisResponse
from app.observability.metrics import predictions_total

logger = logging.getLogger("iris_api")

router = APIRouter(tags=["Predição"], dependencies=[Depends(get_current_user)])

MODEL_UNAVAILABLE_DETAIL = "Modelo não carregado. Verifique se os arquivos .pkl estão disponíveis."


@router.post("/predict", response_model=IrisResponse, summary="Prediz a espécie de uma única amostra")
def predict(payload: IrisRequest, model: IrisModel = Depends(get_model)) -> IrisResponse:
    try:
        result = model.predict(payload)
    except ModelNotLoadedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MODEL_UNAVAILABLE_DETAIL
        ) from exc

    predictions_total.labels(classe=result.prediction.classe).inc()
    return result


@router.post(
    "/predict/batch",
    response_model=IrisBatchResponse,
    summary="Prediz a espécie de várias amostras em uma única requisição",
)
def predict_batch(payload: IrisBatchRequest, model: IrisModel = Depends(get_model)) -> IrisBatchResponse:
    try:
        resultados = model.predict_batch(payload.items)
    except ModelNotLoadedError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=MODEL_UNAVAILABLE_DETAIL
        ) from exc

    for resultado in resultados:
        predictions_total.labels(classe=resultado.prediction.classe).inc()

    return IrisBatchResponse(sucesso=True, total=len(resultados), resultados=resultados)

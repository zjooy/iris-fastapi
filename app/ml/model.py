"""Encapsula o carregamento e a inferência do modelo de classificação Iris."""

import logging
import pickle
from pathlib import Path

import numpy as np

from app.models.schemas import IrisPrediction, IrisProbability, IrisRequest, IrisResponse

logger = logging.getLogger("iris_api")


class ModelNotLoadedError(RuntimeError):
    """Levantada quando uma predição é solicitada sem o modelo carregado."""


class IrisModel:
    """Wrapper fino sobre o classificador scikit-learn serializado.

    Mantém `modelo`/`classes` como estado de instância (em vez de globais de
    módulo) para permitir troca do artefato em testes e um carregamento
    controlado pelo ciclo de vida da aplicação (lifespan do FastAPI).
    """

    def __init__(self, model_path: Path, classes_path: Path) -> None:
        self._model_path = model_path
        self._classes_path = classes_path
        self._modelo = None
        self._classes: list[str] | None = None

    @property
    def is_loaded(self) -> bool:
        return self._modelo is not None and self._classes is not None

    def load(self) -> None:
        try:
            with open(self._model_path, "rb") as f:
                self._modelo = pickle.load(f)
            with open(self._classes_path, "rb") as f:
                self._classes = pickle.load(f)
            logger.info("modelo_carregado", extra={"model_path": str(self._model_path)})
        except FileNotFoundError:
            logger.error(
                "modelo_nao_encontrado",
                extra={"model_path": str(self._model_path), "classes_path": str(self._classes_path)},
            )
            self._modelo = None
            self._classes = None

    @staticmethod
    def _to_row(payload: IrisRequest) -> list[float]:
        return [payload.sepal_length, payload.sepal_width, payload.petal_length, payload.petal_width]

    def _build_response(
        self, payload: IrisRequest, prediction_idx: int, probabilities: np.ndarray
    ) -> IrisResponse:
        return IrisResponse(
            sucesso=True,
            prediction=IrisPrediction(
                classe=self._classes[prediction_idx],
                classe_idx=prediction_idx,
            ),
            probability=IrisProbability(
                setosa=round(float(probabilities[0]), 4),
                versicolor=round(float(probabilities[1]), 4),
                virginica=round(float(probabilities[2]), 4),
            ),
            entrada_recebida=payload,
        )

    def predict(self, payload: IrisRequest) -> IrisResponse:
        if not self.is_loaded:
            raise ModelNotLoadedError()
        features = np.array([self._to_row(payload)])
        prediction_idx = int(self._modelo.predict(features)[0])
        probabilities = self._modelo.predict_proba(features)[0]
        return self._build_response(payload, prediction_idx, probabilities)

    def predict_batch(self, items: list[IrisRequest]) -> list[IrisResponse]:
        """Prediz um lote em uma única chamada ao modelo (mais eficiente que
        chamar `predict` em laço, especialmente para lotes grandes)."""
        if not self.is_loaded:
            raise ModelNotLoadedError()
        features = np.array([self._to_row(item) for item in items])
        prediction_idx_arr = self._modelo.predict(features)
        probabilities_arr = self._modelo.predict_proba(features)
        return [
            self._build_response(item, int(prediction_idx_arr[i]), probabilities_arr[i])
            for i, item in enumerate(items)
        ]

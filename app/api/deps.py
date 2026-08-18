"""Dependências compartilhadas entre rotas."""

from fastapi import Request

from app.ml.model import IrisModel


def get_model(request: Request) -> IrisModel:
    """Retorna a instância única do modelo, criada no lifespan da aplicação."""
    return request.app.state.model

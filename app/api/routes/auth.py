"""Rota de autenticação (login mockado com emissão de JWT)."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import Settings, get_settings
from app.core.security import authenticate_user, create_access_token
from app.models.schemas import Token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post(
    "/login",
    response_model=Token,
    summary="Login (usuário mockado) e emissão de token JWT",
    description=(
        "Não há base de usuários real: existe apenas um usuário de demonstração "
        "configurado via variáveis de ambiente (`MOCK_USERNAME` / senha padrão "
        "`demo123`). Use as credenciais para obter um Bearer token válido para "
        "as rotas de predição."
    ),
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings: Settings = Depends(get_settings),
) -> Token:
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=form_data.username)
    return Token(
        access_token=access_token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )

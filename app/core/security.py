"""Autenticação JWT mockada.

Não há banco de dados de usuários: existe um único usuário de demonstração,
definido via configuração (`settings.mock_username` / `mock_password_hash`).
O objetivo deste módulo é demonstrar o fluxo real de autenticação baseada em
JWT (login -> emissão de token -> validação em rotas protegidas) sem a
complexidade de um sistema de identidade completo.

Para transformar isso em autenticação real, bastaria trocar `authenticate_user`
por uma consulta a uma tabela de usuários (mantendo o restante do fluxo igual).
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenPayload(BaseModel):
    sub: str
    exp: datetime


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def authenticate_user(username: str, password: str) -> bool:
    """Valida as credenciais contra o único usuário mockado.

    Retorna True/False em vez de lançar exceção para manter a função pura
    e testável; a rota de login decide como reagir à falha.
    """
    if username != settings.mock_username:
        return False
    return verify_password(password, settings.mock_password_hash)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return TokenPayload(sub=payload["sub"], exp=payload["exp"])


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependência FastAPI que valida o Bearer token e retorna o username."""
    payload = decode_access_token(token)
    return payload.sub

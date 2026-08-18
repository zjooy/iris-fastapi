"""Configurações centrais da aplicação, carregadas de variáveis de ambiente."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Configurações da aplicação.

    Todos os valores podem ser sobrescritos via variáveis de ambiente ou
    arquivo `.env` (ver `.env.example`). Nenhum segredo real deve ser
    commitado no repositório.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Metadados da aplicação
    app_name: str = "API de Classificação de Espécies de Flores Iris"
    app_version: str = "2.0.0"
    environment: str = "development"

    # CORS
    cors_allow_origins: list[str] = ["*"]

    # Modelo de ML
    model_path: Path = BASE_DIR / "app" / "ml" / "artifacts" / "modelo_iris.pkl"
    classes_path: Path = BASE_DIR / "app" / "ml" / "artifacts" / "classes_iris.pkl"
    batch_max_items: int = 100

    # Autenticação JWT (mockada)
    # ATENÇÃO: os valores abaixo são apenas defaults de desenvolvimento.
    # Em produção, defina JWT_SECRET_KEY via variável de ambiente/secret manager.
    jwt_secret_key: str = "dev-secret-key-troque-em-producao-nunca-versione-o-real"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # Usuário mockado (sem banco de dados) usado apenas para demonstrar o fluxo JWT
    mock_username: str = "demo"
    # Hash bcrypt da senha "demo123" (troque via MOCK_PASSWORD_HASH em produção).
    mock_password_hash: str = "$2b$12$KenabROLW1iOYIlJ.jv8Z.7sNNFMGPoag8BjKeolERHMQR3nGSVn2"

    # Observabilidade
    log_level: str = "INFO"
    log_json: bool = True
    metrics_enabled: bool = True

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Retorna a instância cacheada de Settings (evita reparsing a cada import)."""
    return Settings()

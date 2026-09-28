"""
Configurações da aplicação, carregadas de variáveis de ambiente (.env).

Usar pydantic-settings garante validação de tipos e falha rápida (fail-fast)
caso uma variável obrigatória esteja ausente ou mal formatada — em vez de
descobrir isso só quando a chamada à Azure OpenAI falhar em produção.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Metadados da aplicação ---
    app_name: str = "STRIDE Threat Modeling API"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # --- Azure OpenAI ---
    azure_openai_endpoint: str | None = Field(default=None)
    azure_openai_api_key: str | None = Field(default=None)
    azure_openai_deployment: str = Field(default="gpt-4o")
    azure_openai_api_version: str = Field(default="2024-08-01-preview")

    # --- Comportamento do cliente de IA ---
    # Quando não há credenciais Azure configuradas, o sistema usa
    # automaticamente um cliente "mock" determinístico, permitindo rodar,
    # testar e demonstrar o projeto por completo sem custo e sem depender
    # de infraestrutura externa. Pode ser forçado via AI_CLIENT_MODE.
    ai_client_mode: Literal["auto", "azure", "mock"] = "auto"
    ai_max_retries: int = 3
    ai_timeout_seconds: int = 60

    # --- Segurança da API ---
    api_key: str | None = Field(default=None, description="Chave para autenticar chamadas à API (header X-API-Key)")
    max_upload_size_mb: int = 8
    allowed_image_types: tuple[str, ...] = ("image/png", "image/jpeg", "image/webp")

    # --- Rate limiting ---
    rate_limit: str = "20/minute"

    # --- Observabilidade ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    enable_metrics: bool = True

    @field_validator("max_upload_size_mb")
    @classmethod
    def _tamanho_positivo(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_upload_size_mb deve ser positivo")
        return v

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def azure_configurado(self) -> bool:
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)

    @property
    def usar_cliente_mock(self) -> bool:
        if self.ai_client_mode == "mock":
            return True
        if self.ai_client_mode == "azure":
            return False
        # modo "auto": usa mock apenas se Azure não estiver configurado
        return not self.azure_configurado


@lru_cache
def get_settings() -> Settings:
    """Cache das configurações — lidas do ambiente uma única vez por processo."""
    return Settings()

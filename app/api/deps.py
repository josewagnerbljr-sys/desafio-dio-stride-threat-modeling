"""
Dependências injetáveis do FastAPI.

Centralizar a construção do `StrideAnalyzer` (e a escolha entre cliente
Azure real ou mock) aqui, em vez de instanciar direto no endpoint, é o que
torna o endpoint trivialmente testável: nos testes, sobrescrevemos
`get_stride_analyzer` via `app.dependency_overrides` e injetamos um cliente
falso, sem precisar mockar imports internos do módulo de serviço.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header

from app.core.config import Settings, get_settings
from app.core.security import verificar_api_key
from app.services.ai_client import ClienteIA
from app.services.azure_openai_client import AzureOpenAIClient
from app.services.mock_client import ClienteIAMock
from app.services.stride_analyzer import StrideAnalyzer

SettingsDep = Annotated[Settings, Depends(get_settings)]


@lru_cache
def _construir_cliente_ia(usar_mock: bool) -> ClienteIA:
    """
    Cacheado por processo: o cliente HTTP da Azure (ou o mock) é criado uma
    única vez e reutilizado entre requisições, evitando o custo de recriar
    conexões a cada chamada.
    """
    if usar_mock:
        return ClienteIAMock()
    return AzureOpenAIClient(get_settings())


def get_cliente_ia(settings: SettingsDep) -> ClienteIA:
    return _construir_cliente_ia(settings.usar_cliente_mock)


ClienteIADep = Annotated[ClienteIA, Depends(get_cliente_ia)]


def get_stride_analyzer(cliente_ia: ClienteIADep) -> StrideAnalyzer:
    return StrideAnalyzer(cliente_ia)


StrideAnalyzerDep = Annotated[StrideAnalyzer, Depends(get_stride_analyzer)]


def get_request_id(x_request_id: str | None = Header(default=None)) -> str:
    from app.core.logging import novo_request_id

    return x_request_id or novo_request_id()


RequestIdDep = Annotated[str, Depends(get_request_id)]


def exigir_autenticacao(settings: SettingsDep, x_api_key: str | None = Header(default=None)) -> None:
    verificar_api_key(settings, x_api_key)


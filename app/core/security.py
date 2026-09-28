"""
Autenticação simples por chave de API (header `X-API-Key`).

Em vez de deixar a API totalmente aberta, exigimos uma chave configurável
via variável de ambiente — suficiente para um projeto de portfólio/estudo,
documentando claramente no README como evoluir para OAuth2/Azure AD em um
cenário de produção real.

Quando `API_KEY` não está configurada no ambiente, a autenticação é
desabilitada automaticamente (modo de desenvolvimento/demonstração) — outra
aplicação do mesmo princípio de "degradação graciosa" usado no cliente de
IA mock.
"""

from fastapi import Header

from app.core.config import Settings
from app.core.exceptions import AutenticacaoInvalidaError


def verificar_api_key(settings: Settings, x_api_key: str | None = Header(default=None)) -> None:
    if settings.api_key is None:
        return  # autenticação desabilitada (nenhuma API_KEY configurada)

    if x_api_key != settings.api_key:
        raise AutenticacaoInvalidaError("Chave de API ausente ou inválida (header X-API-Key).")

"""
Cliente real de integração com a Azure OpenAI (modelos multimodais,
ex.: gpt-4o), usado quando `AZURE_OPENAI_ENDPOINT` e `AZURE_OPENAI_API_KEY`
estão configurados.

Implementa retry com backoff exponencial (via tenacity) para lidar com
instabilidades transitórias (rate limit 429, timeouts, erros 5xx) sem
propagar falha para o cliente da API logo na primeira tentativa — prática
padrão de engenharia ao integrar com serviços externos de terceiros.
"""

import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncAzureOpenAI,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import Settings
from app.core.exceptions import ProvedorIAIndisponivelError
from app.services.prompts import construir_mensagens

logger = logging.getLogger(__name__)

_ERROS_TRANSITORIOS = (RateLimitError, APITimeoutError, APIConnectionError)


class AzureOpenAIClient:
    """Implementa o Protocol `ClienteIA` usando o SDK oficial da OpenAI apontado para Azure."""

    def __init__(self, settings: Settings):
        if not settings.azure_configurado:
            raise ValueError("Azure OpenAI não configurado (endpoint/api_key ausentes).")

        self._settings = settings
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            timeout=settings.ai_timeout_seconds,
        )

    @property
    def nome_modelo(self) -> str:
        return self._settings.azure_openai_deployment

    async def gerar_analise(self, imagem_base64: str, mime_type: str, prompt_usuario: str | None) -> str:
        mensagens = construir_mensagens(prompt_usuario, imagem_base64, mime_type)
        try:
            return await self._chamar_com_retry(mensagens)
        except _ERROS_TRANSITORIOS as exc:
            logger.error("Falha ao chamar Azure OpenAI após retries", extra={"extra_fields": {"erro": str(exc)}})
            raise ProvedorIAIndisponivelError(
                "O serviço de IA está temporariamente indisponível. Tente novamente em instantes."
            ) from exc
        except APIStatusError as exc:
            logger.error("Erro da API Azure OpenAI", extra={"extra_fields": {"status": exc.status_code}})
            raise ProvedorIAIndisponivelError(f"Erro do provedor de IA (HTTP {exc.status_code}).") from exc

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(_ERROS_TRANSITORIOS),
    )
    async def _chamar_com_retry(self, mensagens: list[dict]) -> str:
        resposta = await self._client.chat.completions.create(
            model=self._settings.azure_openai_deployment,
            messages=mensagens,
            temperature=0.2,  # baixa temperatura: queremos consistência, não criatividade
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
        conteudo = resposta.choices[0].message.content
        if not conteudo:
            raise ProvedorIAIndisponivelError("O modelo retornou uma resposta vazia.")
        return conteudo

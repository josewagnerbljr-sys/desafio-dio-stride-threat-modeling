"""
Serviço central que orquestra a análise STRIDE: valida a imagem de entrada,
delega a geração ao cliente de IA configurado (Azure real ou mock) e
garante que a resposta seja um `RelatorioSTRIDE` validado — nunca texto
solto.

Esta camada de serviço é o coração da confiabilidade do sistema: LLMs
ocasionalmente retornam JSON quase-válido (aspas erradas, texto extra
antes/depois, chave faltando). Em vez de deixar isso vazar como erro 500
genérico para o cliente da API, tentamos uma extração/reparo best-effort
antes de desistir — e só então levantamos uma exceção de domínio clara.
"""

import json
import logging
import re
import time

from pydantic import ValidationError

from app.core.exceptions import RespostaIAInvalidaError
from app.schemas.threat_model import RelatorioSTRIDE
from app.services.ai_client import ClienteIA

logger = logging.getLogger(__name__)

_PADRAO_BLOCO_JSON = re.compile(r"\{.*\}", re.DOTALL)


class StrideAnalyzer:
    """Caso de uso: 'gerar relatório STRIDE a partir de uma imagem de diagrama'."""

    def __init__(self, cliente_ia: ClienteIA):
        self._cliente_ia = cliente_ia

    @property
    def modelo_utilizado(self) -> str:
        return self._cliente_ia.nome_modelo

    async def analisar(
        self, imagem_base64: str, mime_type: str, prompt_usuario: str | None = None
    ) -> tuple[RelatorioSTRIDE, int]:
        """
        Retorna o relatório validado e o tempo de processamento em
        milissegundos (útil para observabilidade/metadados de resposta).
        """
        inicio = time.perf_counter()
        texto_bruto = await self._cliente_ia.gerar_analise(imagem_base64, mime_type, prompt_usuario)
        relatorio = self._parsear_com_reparo(texto_bruto)
        tempo_ms = int((time.perf_counter() - inicio) * 1000)
        return relatorio, tempo_ms

    def _parsear_com_reparo(self, texto_bruto: str) -> RelatorioSTRIDE:
        # Tentativa 1: parsing direto (caminho feliz — esperado na maioria
        # das vezes, já que instruímos response_format=json_object).
        try:
            return RelatorioSTRIDE.model_validate_json(texto_bruto)
        except (ValidationError, json.JSONDecodeError) as erro_inicial:
            logger.warning(
                "Resposta do modelo não é JSON válido de primeira; tentando reparo.",
                extra={"extra_fields": {"erro": str(erro_inicial)}},
            )

        # Tentativa 2: extrair apenas o maior bloco {...} do texto, caso o
        # modelo tenha incluído markdown (```json ... ```) ou comentário.
        correspondencia = _PADRAO_BLOCO_JSON.search(texto_bruto)
        if correspondencia:
            try:
                return RelatorioSTRIDE.model_validate_json(correspondencia.group(0))
            except (ValidationError, json.JSONDecodeError) as erro_reparo:
                logger.error(
                    "Falha ao reparar resposta do modelo.",
                    extra={"extra_fields": {"erro": str(erro_reparo)}},
                )
                raise RespostaIAInvalidaError(
                    "O modelo de IA retornou uma resposta em formato inesperado, "
                    "mesmo após tentativa de reparo automático."
                ) from erro_reparo

        raise RespostaIAInvalidaError(
            "O modelo de IA não retornou nenhum conteúdo JSON identificável na resposta."
        )

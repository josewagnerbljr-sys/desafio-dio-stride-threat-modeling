import json

import pytest

from app.core.exceptions import RespostaIAInvalidaError
from app.schemas.threat_model import CategoriaSTRIDE, RelatorioSTRIDE, Severidade
from app.services.stride_analyzer import StrideAnalyzer

RELATORIO_VALIDO = {
    "resumo_arquitetura": "Sistema simples.",
    "componentes": [{"nome": "API", "tipo": "processo"}],
    "ameacas": [
        {
            "categoria": "Spoofing",
            "componente_afetado": "API",
            "titulo": "Sem autenticacao",
            "descricao": "Qualquer um pode chamar a API.",
            "severidade": "Alta",
            "mitigacoes": ["Usar OAuth2", "  "],
        }
    ],
}


class ClienteFalso:
    def __init__(self, resposta: str):
        self._resposta = resposta

    nome_modelo = "falso"

    async def gerar_analise(self, imagem_base64, mime_type, prompt_usuario):
        return self._resposta


@pytest.mark.asyncio
async def test_parse_direto():
    a = StrideAnalyzer(ClienteFalso(json.dumps(RELATORIO_VALIDO)))
    relatorio, tempo = await a.analisar("x", "image/png")
    assert relatorio.ameacas[0].categoria == CategoriaSTRIDE.SPOOFING
    assert relatorio.ameacas[0].mitigacoes == ["Usar OAuth2"]  # item vazio removido
    assert tempo >= 0


@pytest.mark.asyncio
async def test_reparo_de_json_dentro_de_markdown():
    texto = "Aqui está:\n```json\n" + json.dumps(RELATORIO_VALIDO) + "\n```"
    a = StrideAnalyzer(ClienteFalso(texto))
    relatorio, _ = await a.analisar("x", "image/png")
    assert len(relatorio.ameacas) == 1


@pytest.mark.asyncio
async def test_resposta_sem_json_levanta_erro_de_dominio():
    a = StrideAnalyzer(ClienteFalso("desculpe, não consigo ajudar"))
    with pytest.raises(RespostaIAInvalidaError):
        await a.analisar("x", "image/png")


@pytest.mark.asyncio
async def test_json_com_schema_errado_levanta_erro_de_dominio():
    ruim = dict(RELATORIO_VALIDO)
    ruim["ameacas"] = [{"categoria": "Inventada"}]
    a = StrideAnalyzer(ClienteFalso(json.dumps(ruim)))
    with pytest.raises(RespostaIAInvalidaError):
        await a.analisar("x", "image/png")


def test_ordenacao_e_contagens():
    r = RelatorioSTRIDE.model_validate(
        {
            "resumo_arquitetura": "x",
            "ameacas": [
                {"categoria": "Tampering", "componente_afetado": "a", "titulo": "t", "descricao": "d", "severidade": "Baixa"},
                {"categoria": "Spoofing", "componente_afetado": "a", "titulo": "t", "descricao": "d", "severidade": "Crítica"},
            ],
        }
    )
    assert r.ameacas_ordenadas_por_severidade()[0].severidade == Severidade.CRITICA
    assert r.contagem_por_categoria()["Spoofing"] == 1
    assert r.contagem_por_severidade()["Baixa"] == 1

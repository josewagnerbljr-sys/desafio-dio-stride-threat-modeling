"""
Schemas Pydantic que definem o contrato da API — tanto o que o modelo de IA
deve retornar (validado rigoramente) quanto o que a API expõe ao cliente.

Usar Pydantic aqui não é só "boa prática de FastAPI": é a peça central da
confiabilidade do sistema. LLMs retornam texto; forçamos esse texto a
passar por um schema estrito antes de qualquer coisa ser considerada uma
"ameaça válida" — se o modelo alucinar um campo ou tipo errado, a validação
falha de forma explícita, em vez de propagar dado ruim silenciosamente.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class CategoriaSTRIDE(StrEnum):
    SPOOFING = "Spoofing"
    TAMPERING = "Tampering"
    REPUDIATION = "Repudiation"
    INFORMATION_DISCLOSURE = "Information Disclosure"
    DENIAL_OF_SERVICE = "Denial of Service"
    ELEVATION_OF_PRIVILEGE = "Elevation of Privilege"


class Severidade(StrEnum):
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    CRITICA = "Crítica"


# Ordem usada para ordenar ameaças da mais crítica para a menos crítica
_ORDEM_SEVERIDADE = {
    Severidade.CRITICA: 0,
    Severidade.ALTA: 1,
    Severidade.MEDIA: 2,
    Severidade.BAIXA: 3,
}


class ComponenteDiagrama(BaseModel):
    """Um componente de arquitetura identificado no diagrama (ex.: 'API Gateway')."""

    nome: str = Field(..., min_length=1, max_length=200)
    tipo: str = Field(..., description="Ex.: 'processo', 'armazenamento de dados', 'ator externo', 'fluxo de dados'")
    descricao: str | None = Field(default=None, max_length=1000)


class Ameaca(BaseModel):
    """Uma ameaça individual identificada, seguindo a metodologia STRIDE."""

    categoria: CategoriaSTRIDE
    componente_afetado: str = Field(..., min_length=1, max_length=200)
    titulo: str = Field(..., min_length=1, max_length=200)
    descricao: str = Field(..., min_length=1, max_length=2000)
    severidade: Severidade
    mitigacoes: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("mitigacoes")
    @classmethod
    def _pelo_menos_uma_mitigacao_recomendada(cls, v: list[str]) -> list[str]:
        return [m.strip() for m in v if m and m.strip()]


class RelatorioSTRIDE(BaseModel):
    """
    Estrutura completa retornada pelo modelo de IA — este é o "contrato"
    que o prompt de engenharia (ver services/prompts.py) instrui o modelo
    a preencher, e que validamos rigidamente na resposta (ver
    services/stride_analyzer.py).
    """

    resumo_arquitetura: str = Field(..., min_length=1, max_length=2000)
    componentes: list[ComponenteDiagrama] = Field(default_factory=list, max_length=50)
    ameacas: list[Ameaca] = Field(default_factory=list, max_length=100)

    def ameacas_ordenadas_por_severidade(self) -> list[Ameaca]:
        return sorted(self.ameacas, key=lambda a: _ORDEM_SEVERIDADE[a.severidade])

    def contagem_por_categoria(self) -> dict[str, int]:
        contagem = {c.value: 0 for c in CategoriaSTRIDE}
        for ameaca in self.ameacas:
            contagem[ameaca.categoria.value] += 1
        return contagem

    def contagem_por_severidade(self) -> dict[str, int]:
        contagem = {s.value: 0 for s in Severidade}
        for ameaca in self.ameacas:
            contagem[ameaca.severidade.value] += 1
        return contagem


class MetadadosAnalise(BaseModel):
    """Metadados operacionais sobre a análise executada (para auditoria e observabilidade)."""

    request_id: str
    modelo_utilizado: str
    modo_cliente: str = Field(..., description="'azure' ou 'mock'")
    tempo_processamento_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AnaliseAmeacaResponse(BaseModel):
    """Corpo de resposta do endpoint POST /api/v1/analyze."""

    relatorio: RelatorioSTRIDE
    metadados: MetadadosAnalise


class ErroResponse(BaseModel):
    """Corpo de resposta padronizado para erros da API."""

    erro: str
    detalhes: str | None = None
    request_id: str | None = None


class HealthResponse(BaseModel):
    status: str
    versao: str
    modo_cliente_ia: str

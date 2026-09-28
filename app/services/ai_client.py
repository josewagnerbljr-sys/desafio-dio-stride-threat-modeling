"""
Interface (Protocol) que qualquer cliente de IA usado pela aplicação deve
implementar.

Programar contra essa interface — em vez de acoplar o serviço diretamente
ao SDK da Azure — é o que permite trocar entre o cliente real e o cliente
mock (ou, futuramente, outro provedor como AWS Bedrock ou um modelo local)
sem qualquer alteração em `stride_analyzer.py`. É o princípio de Inversão
de Dependência aplicado a um cenário real de integração com LLMs.
"""

from typing import Protocol


class ClienteIA(Protocol):
    """Contrato mínimo: recebe uma imagem e devolve o texto bruto da resposta do modelo."""

    async def gerar_analise(self, imagem_base64: str, mime_type: str, prompt_usuario: str | None) -> str:
        """Retorna a resposta textual bruta do modelo (JSON esperado, ainda não parseado)."""
        ...

    @property
    def nome_modelo(self) -> str:
        ...

"""
Exceções de domínio da aplicação.

Ter exceções tipadas (em vez de HTTPException genérica espalhada pelo
código) separa a camada de negócio da camada HTTP: os serviços levantam
essas exceções sem saber nada sobre FastAPI, e os handlers registrados em
main.py convertem cada uma para o status HTTP e corpo de resposta corretos.
"""


class ErroDominio(Exception):
    """Classe-base para todas as exceções de domínio da aplicação."""


class ImagemInvalidaError(ErroDominio):
    """Levantada quando o arquivo enviado não é uma imagem válida/suportada."""


class ImagemMuitoGrandeError(ErroDominio):
    """Levantada quando o arquivo enviado excede o tamanho máximo permitido."""


class ProvedorIAIndisponivelError(ErroDominio):
    """Levantada quando o provedor de IA (Azure OpenAI) falha ou está fora do ar."""


class RespostaIAInvalidaError(ErroDominio):
    """
    Levantada quando o modelo retorna uma resposta que não pôde ser
    interpretada como um relatório STRIDE estruturado válido, mesmo após
    as tentativas de repetição (retries).
    """


class AutenticacaoInvalidaError(ErroDominio):
    """Levantada quando a chave de API informada é inválida ou está ausente."""

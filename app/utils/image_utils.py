"""
Validação e preparo da imagem enviada pelo usuário.

Validar o arquivo antes de qualquer chamada à API de IA evita gastar
tempo/custo com uma requisição que sabemos que vai falhar (arquivo vazio,
formato não suportado, tamanho acima do limite) — e devolve um erro 4xx
claro ao cliente em vez de um 500 genérico vindo de camadas mais internas.
"""

import base64
import io

from PIL import Image, UnidentifiedImageError

from app.core.config import Settings
from app.core.exceptions import ImagemInvalidaError, ImagemMuitoGrandeError


def validar_e_codificar_imagem(conteudo: bytes, mime_type: str | None, settings: Settings) -> str:
    """
    Valida o arquivo enviado e retorna sua representação em base64, pronta
    para ser embutida no prompt multimodal.

    Levanta `ImagemMuitoGrandeError` ou `ImagemInvalidaError` (ambas
    exceções de domínio) quando a validação falha.
    """
    if not conteudo:
        raise ImagemInvalidaError("O arquivo enviado está vazio.")

    if len(conteudo) > settings.max_upload_size_bytes:
        raise ImagemMuitoGrandeError(
            f"O arquivo excede o tamanho máximo permitido de {settings.max_upload_size_mb}MB."
        )

    if mime_type not in settings.allowed_image_types:
        raise ImagemInvalidaError(
            f"Tipo de arquivo '{mime_type}' não suportado. "
            f"Tipos aceitos: {', '.join(settings.allowed_image_types)}."
        )

    # Verifica que o conteúdo é, de fato, uma imagem decodificável — e não
    # apenas um arquivo com a extensão/content-type certos (defesa contra
    # upload malformado ou spoofing de mimetype).
    try:
        imagem = Image.open(io.BytesIO(conteudo))
        imagem.verify()
    except UnidentifiedImageError as exc:
        raise ImagemInvalidaError("O arquivo enviado não é uma imagem válida.") from exc

    return base64.b64encode(conteudo).decode("ascii")

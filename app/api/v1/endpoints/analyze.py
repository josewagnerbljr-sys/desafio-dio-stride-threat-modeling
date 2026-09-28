"""Endpoint principal: recebe um diagrama de arquitetura e devolve o relatório STRIDE."""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import PlainTextResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import RequestIdDep, SettingsDep, StrideAnalyzerDep, exigir_autenticacao
from app.core.exceptions import (
    ImagemInvalidaError,
    ImagemMuitoGrandeError,
    ProvedorIAIndisponivelError,
    RespostaIAInvalidaError,
)
from app.schemas.threat_model import AnaliseAmeacaResponse, MetadadosAnalise
from app.services.report_renderer import renderizar_markdown
from app.utils.image_utils import validar_e_codificar_imagem

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post(
    "/analyze",
    response_model=AnaliseAmeacaResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Analisa um diagrama de arquitetura e gera um relatório de ameaças STRIDE",
    tags=["Análise de Ameaças"],
    dependencies=[Depends(exigir_autenticacao)],
)
@limiter.limit("20/minute")
async def analisar_diagrama(
    request: Request,  # exigido pelo slowapi para leitura do IP do cliente
    analyzer: StrideAnalyzerDep,
    settings: SettingsDep,
    request_id: RequestIdDep,
    arquivo: UploadFile = File(..., description="Imagem do diagrama de arquitetura (PNG, JPEG ou WEBP)"),
    prompt: str | None = None,
    formato: Literal["json", "markdown"] = "json",
):
    conteudo = await arquivo.read()

    try:
        imagem_base64 = validar_e_codificar_imagem(conteudo, arquivo.content_type, settings)
    except ImagemMuitoGrandeError as exc:
        raise HTTPException(413, detail=str(exc)) from exc
    except ImagemInvalidaError as exc:
        raise HTTPException(422, detail=str(exc)) from exc

    logger.info(
        "Iniciando análise STRIDE",
        extra={"extra_fields": {"request_id": request_id, "tamanho_bytes": len(conteudo)}},
    )

    try:
        relatorio, tempo_ms = await analyzer.analisar(
            imagem_base64=imagem_base64,
            mime_type=arquivo.content_type or "image/png",
            prompt_usuario=prompt,
        )
    except ProvedorIAIndisponivelError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except RespostaIAInvalidaError as exc:
        raise HTTPException(422, detail=str(exc)) from exc

    logger.info(
        "Análise STRIDE concluída",
        extra={"extra_fields": {"request_id": request_id, "qtd_ameacas": len(relatorio.ameacas), "tempo_ms": tempo_ms}},
    )

    if formato == "markdown":
        return PlainTextResponse(renderizar_markdown(relatorio), media_type="text/markdown; charset=utf-8")

    return AnaliseAmeacaResponse(
        relatorio=relatorio,
        metadados=MetadadosAnalise(
            request_id=request_id,
            modelo_utilizado=analyzer.modelo_utilizado,
            modo_cliente="mock" if settings.usar_cliente_mock else "azure",
            tempo_processamento_ms=tempo_ms,
        ),
    )

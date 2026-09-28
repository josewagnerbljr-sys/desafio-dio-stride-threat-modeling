"""
Ponto de entrada da aplicação FastAPI.

Aqui ficam apenas a montagem da aplicação (middlewares, handlers de erro,
rotas, métricas). Nenhuma regra de negócio mora neste arquivo.
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.endpoints.analyze import limiter
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AutenticacaoInvalidaError
from app.core.logging import configurar_logging, novo_request_id, request_id_ctx

logger = logging.getLogger(__name__)

REQUISICOES_TOTAL = Counter(
    "http_requests_total", "Total de requisições HTTP", ["metodo", "rota", "status"]
)
LATENCIA_REQUISICAO = Histogram(
    "http_request_duration_seconds", "Latência das requisições HTTP em segundos", ["metodo", "rota"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configurar_logging(settings.log_level)
    logger.info(
        "Aplicação iniciada",
        extra={
            "extra_fields": {
                "versao": settings.app_version,
                "ambiente": settings.environment,
                "modo_cliente_ia": "mock" if settings.usar_cliente_mock else "azure",
            }
        },
    )
    yield
    logger.info("Aplicação encerrada")


def criar_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "API que recebe a imagem de um diagrama de arquitetura e gera "
            "automaticamente uma análise de ameaças com a metodologia STRIDE, "
            "usando Azure OpenAI (GPT-4o multimodal) e prompt engineering."
        ),
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(AutenticacaoInvalidaError)
    async def _handler_autenticacao(request: Request, exc: AutenticacaoInvalidaError):
        return JSONResponse(status_code=401, content={"erro": "Não autorizado", "detalhes": str(exc)})

    @app.middleware("http")
    async def _middleware_observabilidade(request: Request, call_next):
        rid = request.headers.get("x-request-id") or novo_request_id()
        token = request_id_ctx.set(rid)
        inicio = time.perf_counter()
        try:
            resposta = await call_next(request)
        finally:
            duracao = time.perf_counter() - inicio
            rota = request.scope.get("route").path if request.scope.get("route") else request.url.path
            if settings.enable_metrics:
                LATENCIA_REQUISICAO.labels(request.method, rota).observe(duracao)
            request_id_ctx.reset(token)
        if settings.enable_metrics:
            REQUISICOES_TOTAL.labels(request.method, rota, resposta.status_code).inc()
        resposta.headers["X-Request-ID"] = rid
        return resposta

    app.include_router(api_router, prefix="/api/v1")

    if settings.enable_metrics:

        @app.get("/metrics", include_in_schema=False)
        def metrics() -> Response:
            return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app


app = criar_app()

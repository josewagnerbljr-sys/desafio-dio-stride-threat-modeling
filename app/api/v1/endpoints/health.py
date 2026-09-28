from fastapi import APIRouter

from app.api.deps import SettingsDep
from app.schemas.threat_model import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifica se a API está no ar e como está configurada",
    tags=["Observabilidade"],
)
def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        versao=settings.app_version,
        modo_cliente_ia="mock" if settings.usar_cliente_mock else "azure",
    )

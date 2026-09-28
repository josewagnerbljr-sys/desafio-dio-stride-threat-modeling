import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.config import get_settings
from app.main import criar_app


@pytest.fixture(autouse=True)
def _ambiente_limpo(monkeypatch):
    """Garante que os testes rodem sempre em modo mock, sem chave de API."""
    monkeypatch.setenv("AI_CLIENT_MODE", "mock")
    monkeypatch.delenv("API_KEY", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    return TestClient(criar_app())


@pytest.fixture
def png_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buf, format="PNG")
    return buf.getvalue()

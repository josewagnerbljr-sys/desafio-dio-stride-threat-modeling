def _post(client, conteudo, tipo="image/png", headers=None):
    return client.post(
        "/api/v1/analyze",
        files={"arquivo": ("diagrama.png", conteudo, tipo)},
        headers=headers or {},
    )


def test_analise_completa_retorna_relatorio_stride(client, png_bytes):
    r = _post(client, png_bytes)
    assert r.status_code == 200
    corpo = r.json()
    categorias = {a["categoria"] for a in corpo["relatorio"]["ameacas"]}
    assert categorias == {
        "Spoofing", "Tampering", "Repudiation",
        "Information Disclosure", "Denial of Service", "Elevation of Privilege",
    }
    assert corpo["metadados"]["modo_cliente"] == "mock"


def test_arquivo_vazio_retorna_422(client):
    assert _post(client, b"").status_code == 422


def test_tipo_nao_suportado_retorna_422(client, png_bytes):
    assert _post(client, png_bytes, tipo="application/pdf").status_code == 422


def test_conteudo_que_nao_e_imagem_retorna_422(client):
    assert _post(client, b"isto nao e uma imagem").status_code == 422


def test_arquivo_grande_demais_retorna_413(client, monkeypatch, png_bytes):
    from app.core.config import get_settings

    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "1")
    get_settings.cache_clear()
    grande = png_bytes + b"0" * (1024 * 1024 + 1)
    assert _post(client, grande).status_code == 413


def test_autenticacao_exigida_quando_api_key_configurada(client, monkeypatch, png_bytes):
    from app.core.config import get_settings

    monkeypatch.setenv("API_KEY", "segredo")
    get_settings.cache_clear()
    assert _post(client, png_bytes).status_code == 401
    assert _post(client, png_bytes, headers={"X-API-Key": "errada"}).status_code == 401
    assert _post(client, png_bytes, headers={"X-API-Key": "segredo"}).status_code == 200


def test_formato_markdown(client, png_bytes):
    r = client.post(
        "/api/v1/analyze?formato=markdown",
        files={"arquivo": ("d.png", png_bytes, "image/png")},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/markdown")
    assert "# Relatório de Ameaças STRIDE" in r.text
    assert "Mitigações recomendadas" in r.text

def test_health_ok(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["status"] == "ok"
    assert corpo["modo_cliente_ia"] == "mock"


def test_metrics_exposto(client):
    client.get("/api/v1/health")
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text


def test_request_id_devolvido_no_header(client):
    r = client.get("/api/v1/health", headers={"X-Request-ID": "abc123"})
    assert r.headers["X-Request-ID"] == "abc123"

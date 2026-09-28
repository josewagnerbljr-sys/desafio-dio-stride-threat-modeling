# ---------- Estágio 1: instala dependências ----------
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- Estágio 2: imagem final enxuta ----------
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# Usuário não-root: reduz o impacto de uma eventual exploração do container
RUN useradd --create-home --uid 1000 appuser
COPY --from=builder /install /usr/local
COPY app ./app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

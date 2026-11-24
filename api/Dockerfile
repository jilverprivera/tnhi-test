# Docket API: FastAPI + local OCR (Tesseract, Spanish). No document leaves the container.
FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1

WORKDIR /srv/api
COPY api/pyproject.toml api/uv.lock api/.python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY api/app ./app
# Client data used to seed the ledger and catalogs (read-only inside the image)
COPY material /srv/material
# No TAC_* values are baked in: docker-compose.yml / render.yaml set every variable.

RUN useradd --create-home docket && mkdir -p /data && chown docket /data
USER docket
VOLUME ["/data"]
EXPOSE 8000
CMD ["sh", "-c", "uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

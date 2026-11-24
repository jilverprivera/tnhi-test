# Docket — radicación asistida para Terminales Andinas de Carga

Docket hace el trabajo de radicación de la bandeja de correo. Lee cada correo y sus adjuntos: PDF nativos, PDF escaneados con OCR local, Word, Excel, HTML y el cuerpo del mensaje. Por cada documento propone:

- qué es y qué datos importan;
- a qué dependencia va y qué acción toca;
- cuándo vence, en días hábiles de Colombia.

Aplica las reglas que contó Martha: maestro de proveedores, OC, duplicados, cambio de cuenta (fraude), viáticos TH-F-012 y plazos de derechos de petición y oficios. **Nada se radica ni se reenvía sin que Martha lo apruebe.** Lo que el sistema no puede decidir con seguridad queda en "Requiere revisión", con el motivo. Al aprobar, el sistema asigna el consecutivo `TAC-2026-ER-#####` y continúa el **mismo libro en Excel** que usan Contabilidad y Jurídica.

La Dra. Herrera ve cada semana qué vence, en la app o preguntándole a su asistente de IA a través del servidor **MCP** (solo lectura).

> Fecha del caso: **18 de noviembre de 2026**. Empresa, personas, NIT, cuentas y correos son ficticios.

| | |
|---|---|
| `api/` | Backend en Python 3.12 con FastAPI. Usa *vertical slices* con arquitectura hexagonal: `catalogs`, `ingestion`, `classification`, `filing`, `ledger`, `deadlines`, `audit`. Incluye el servidor MCP. |
| `web/` | Frontend en Next.js 16, como PWA responsive. Usa *screaming architecture* (`inbox`, `document-review`, `ledger`, `deadlines`, `settings`, `session`) con atomic design, Tailwind v4 y shadcn/ui. |
| `docs/` | Documentación en español (`docs/es/`) e inglés (`docs/en/`). Una guía por feature y los entregables de la entrevista en `deliverables/`. |
| `material/` | El material del reto. Es **solo lectura**: la app trabaja sobre copias. |

## Correr en local

Requisitos: [uv](https://docs.astral.sh/uv/), nvm (Node 22, ver `.nvmrc`) y pnpm 10.18. Para leer PDF escaneados hace falta Tesseract (`brew install tesseract tesseract-lang`). Sin Tesseract, los escaneados quedan en revisión, nunca adivinados.

```bash
# 1) API → http://localhost:8000/docs
cd api
uv sync                                          # crea api/.venv e instala dependencias
uv run uvicorn app.main:app --reload --port 8000
# (alternativa: source .venv/bin/activate && uvicorn app.main:app --reload)

# 2) Web → http://localhost:3000   (otra terminal)
cd web
nvm use && pnpm install
DOCKET_API_URL=http://localhost:8000 pnpm dev
```

Códigos de acceso de demostración: `martha-demo` (radicación) y `herrera-demo` (coordinación). En la Bandeja, **"Leer buzón"** importa los 16 correos de `material/2-bandeja-de-entrada`. Configuración: `api/.env.example` y `web/.env.example`.

Otras formas de usarlo:

```bash
cd api
uv run python -m app.cli process --data-dir /tmp/docket --approve-all   # todo el buzón por consola
uv run python -m app.mcp.server                                         # MCP por stdio (Claude Desktop / Claude Code)
uv run python -m app.mcp.server --http                                  # MCP por HTTP en 127.0.0.1:8001
```

Para registrar el servidor MCP en Claude Code: `claude mcp add docket -- uv run --project /ruta/a/api python -m app.mcp.server`. Después basta con preguntar *"¿qué vence esta semana?"*.

## Docker (on-prem: los datos no salen de TAC)

```bash
docker compose up --build     # web :3000, API :8000 (con Tesseract en español), datos en el volumen docket-data
```

Para la demo en la nube hay dos opciones. `render.yaml` despliega la API en Docker en Render, con disco persistente. El frontend va a Vercel: proyecto con raíz `web/` y la variable `DOCKET_API_URL`. Ambas configuraciones están escritas, pero **aún no están desplegadas**.

## Pruebas

Las pruebas **nunca se corren completas de una vez**, para no saturar la RAM. Se corren por lotes con el harness:

```bash
./scripts/harness-verify.sh --api                 # pytest de lo que cambió (lotes de 3, con guarda de RAM)
./scripts/harness-verify.sh --web                 # lint + Jest/RTL de lo que cambió
./scripts/harness-verify.sh --e2e                 # Playwright (levanta API y web reales, workers=1)
./scripts/harness-verify.sh api/tests/golden/test_golden.py   # archivos puntuales
```

Las *golden tests* comparan el resultado con `material/4-para-medirte/esperado-parcial.csv` (8/8) y con la tabla completa `api/tests/golden/esperado-completo.csv`. Esa tabla da 17/17 con OCR, verificado dentro de la imagen Docker: radicados 04818 a 04831.

## Documentación

- Entregables de la entrevista: [`docs/es/deliverables/`](docs/es/deliverables/), empezando por el **resumen ejecutivo** (`00-resumen-ejecutivo.md`).
- Cómo funciona cada parte: [`docs/es/README.md`](docs/es/README.md) · English: [`docs/en/README.md`](docs/en/README.md).
- Reglas del proyecto para agentes: [`CLAUDE.md`](CLAUDE.md) y [`.claude/`](.claude/).

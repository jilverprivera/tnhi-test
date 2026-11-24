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
| `material/` | El material del reto. Es **solo lectura**: la app trabaja sobre copias. |

## Correr en local

Requisitos: [uv](https://docs.astral.sh/uv/), nvm (Node 22, ver `.nvmrc`) y pnpm 10.18. Antes de arrancar, cree `api/.env` y `web/.env.local` con las variables de la sección [Variables](#variables) (los archivos `.env` no se versionan). Para leer PDF escaneados hace falta Tesseract (`brew install tesseract tesseract-lang`). Sin Tesseract, los escaneados quedan en revisión, nunca adivinados.

```bash
# 1) API → http://localhost:8000/docs
cd api
uv sync                                          # crea api/.venv e instala dependencias
uv run uvicorn app.main:app --reload --port 8000
# (alternativa: source .venv/bin/activate && uvicorn app.main:app --reload)

# 2) Web → http://localhost:3000   (otra terminal)
cd web
nvm use && pnpm install
pnpm dev
```

Los códigos de acceso son los que ponga en `TAC_CLERK_TOKEN` (radicación) y `TAC_COORDINATOR_TOKEN` (coordinación). En la Bandeja, **"Leer buzón"** importa los 16 correos de `material/2-bandeja-de-entrada`.

## Variables

**Ninguna variable tiene valor por defecto en el código**: cada una es lo que diga el entorno o queda indefinida. Si falta una obligatoria, la API no arranca y dice cuál (`TAC_DATA_DIR is not set`). El API lee `api/.env` sin importar desde dónde se inicie, y las rutas relativas se toman desde `api/`.

`api/.env` (valores para correr en local):

```bash
# Obligatorias
TAC_DATA_DIR=data
TAC_DATABASE_URL=sqlite:///data/tac.db
TAC_INBOX_DIR=../material/2-bandeja-de-entrada
TAC_SUPPLIERS_CSV=../material/3-datos-del-cliente/maestro-proveedores.csv
TAC_DEPARTMENTS_CSV=../material/3-datos-del-cliente/dependencias.csv
TAC_LEDGER_XLSX=../material/3-datos-del-cliente/libro-radicacion-2026.xlsx
TAC_COMPANY_NIT=900.100.200-3
TAC_FILING_PREFIX=TAC-2026-ER-
TAC_OCR_LANGUAGE=spa
TAC_MIN_OCR_CONFIDENCE=70            # por debajo, el escaneado va a revisión
TAC_MIN_CLASSIFICATION_MARGIN=2      # por debajo, el tipo se considera dudoso
# Opcionales: si faltan, eso queda apagado
TAC_TODAY=2026-11-18                 # sin ella: la fecha real
TAC_CLERK_TOKEN=martha-demo          # sin ella: ese rol no puede entrar
TAC_COORDINATOR_TOKEN=herrera-demo
TAC_WORKER_ENABLED=true              # procesador de la cola de importación
TAC_WORKER_POLL_SECONDS=0.5          # obligatoria si el procesador está encendido
TAC_LEDGER_SYNC_SECONDS=30           # sincronización con el Excel compartido; sin ella: solo al aprobar/exportar
TAC_EXTRA_HOLIDAYS=[]                # festivos adicionales (lista JSON)
TAC_CORS_ORIGINS=["http://localhost:3000"]   # solo si un navegador llama al API directamente
TAC_LLM_ENABLED=false                # IA opcional: solo con las tres variables
TAC_ANTHROPIC_API_KEY=
TAC_LLM_MODEL=claude-haiku-5-5
TAC_MCP_HOST=127.0.0.1               # obligatorias solo para MCP por HTTP
TAC_MCP_PORT=8001
```

`web/.env.local`:

```bash
DOCKET_API_URL=http://localhost:8000     # obligatoria
DOCKET_DEMO_CLERK_CODE=martha-demo       # opcional: pista en la pantalla de ingreso (igual a TAC_CLERK_TOKEN)
DOCKET_DEMO_COORDINATOR_CODE=herrera-demo
```

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

`docker compose` lee `api/.env` y `web/.env.local`; las rutas dentro del contenedor las fija `docker-compose.yml`.

## Despliegue en la nube (demo con datos ficticios)

La API va a **Render** (Docker, con Tesseract y disco persistente) y la web a **Vercel**. El navegador nunca llama al API: Next.js lo llama desde el servidor, así que no hace falta CORS.

**1. API en Render** (`render.yaml`)

1. En Render: *New → Blueprint* y elija este repositorio. Render lee `render.yaml` y crea `docket-api` en Virginia, plan *starter*, con un disco de 1 GB en `/data`.
2. En el primer despliegue Render pide los valores marcados `sync: false`: `TAC_CLERK_TOKEN` y `TAC_COORDINATOR_TOKEN` (los códigos de acceso que usted elija) y, si va a usar IA, `TAC_ANTHROPIC_API_KEY` (y cambie `TAC_LLM_ENABLED` a `true`).
3. Al terminar, `https://<servicio>.onrender.com/api/health` debe responder `HEALTHY`. Cada push a `main` vuelve a desplegar.

**2. Web en Vercel** (`web/vercel.json`)

1. En Vercel: *Add New → Project* e importe este repositorio. En **Root Directory** elija `web` (Vercel detecta Next.js, pnpm y Node 22).
2. En *Environment Variables* (Production y Preview):
   - `DOCKET_API_URL` = la URL de Render, sin `/` al final;
   - opcional, `DOCKET_DEMO_CLERK_CODE` y `DOCKET_DEMO_COORDINATOR_CODE` con los mismos códigos de Render, para mostrarlos como pista al ingresar.
3. *Deploy*. Las funciones corren en `iad1`, junto a la API en Virginia. Cada push a `main` vuelve a desplegar.

Si cambia una variable en Vercel, hay que volver a desplegar para que tome efecto.

## Pruebas

Las pruebas **nunca se corren completas de una vez**, para no saturar la RAM. Se corren por lotes con el harness:

```bash
./scripts/harness-verify.sh --api                 # pytest de lo que cambió (lotes de 3, con guarda de RAM)
./scripts/harness-verify.sh --web                 # lint + Jest/RTL de lo que cambió
./scripts/harness-verify.sh --e2e                 # Playwright (levanta API y web reales, workers=1)
./scripts/harness-verify.sh api/tests/golden/test_golden.py   # archivos puntuales
```

Las *golden tests* comparan el resultado con `material/4-para-medirte/esperado-parcial.csv` (8/8) y con la tabla completa `api/tests/golden/esperado-completo.csv`. Esa tabla da 17/17 con OCR, verificado dentro de la imagen Docker: radicados 04818 a 04831.

## Reglas del proyecto

Reglas para agentes: [`CLAUDE.md`](CLAUDE.md) y [`.claude/`](.claude/).

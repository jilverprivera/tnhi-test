import { defineConfig, devices } from "@playwright/test";
import os from "node:os";
import path from "node:path";

const API_PORT = 8010;
const WEB_PORT = 3100;
// Fresh data dir per run: the real API, real rules, the sample mailbox; material/ stays read-only.
const DATA_DIR = path.join(os.tmpdir(), `docket-e2e-${Date.now()}`);
const CLIENT_DATA = path.resolve(__dirname, "../material/3-datos-del-cliente");
// Every TAC_* explicit (the API has no defaults); these win over api/.env, so E2E never touches dev data.
const API_ENV = {
  TAC_DATA_DIR: DATA_DIR,
  TAC_DATABASE_URL: `sqlite:///${path.join(DATA_DIR, "tac.db")}`,
  TAC_INBOX_DIR: path.resolve(__dirname, "../material/2-bandeja-de-entrada"),
  TAC_SUPPLIERS_CSV: path.join(CLIENT_DATA, "maestro-proveedores.csv"),
  TAC_DEPARTMENTS_CSV: path.join(CLIENT_DATA, "dependencias.csv"),
  TAC_LEDGER_XLSX: path.join(CLIENT_DATA, "libro-radicacion-2026.xlsx"),
  TAC_TODAY: "2026-11-18",
  TAC_COMPANY_NIT: "900.100.200-3",
  TAC_FILING_PREFIX: "TAC-2026-ER-",
  TAC_OCR_LANGUAGE: "spa",
  TAC_MIN_OCR_CONFIDENCE: "70",
  TAC_MIN_CLASSIFICATION_MARGIN: "2",
  TAC_LLM_ENABLED: "false",
  TAC_WORKER_ENABLED: "true",
  TAC_WORKER_POLL_SECONDS: "0.5",
  TAC_LEDGER_SYNC_SECONDS: "0",
  TAC_CLERK_TOKEN: "martha-demo",
  TAC_COORDINATOR_TOKEN: "herrera-demo",
  TAC_CORS_ORIGINS: `["http://localhost:${WEB_PORT}"]`,
};

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1, // never unbounded parallelism (CLAUDE.md guardrail)
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    locale: "es-CO",
    timezoneId: "America/Bogota",
    trace: "retain-on-failure",
  },
  projects: [
    // The clerk's flow first; the coordinator verifies what the clerk filed (shared API per run)
    { name: "desktop", use: { ...devices["Desktop Chrome"] }, testMatch: /filing-flow\.spec\.ts/ },
    {
      name: "coordinator",
      use: { ...devices["Desktop Chrome"] },
      testMatch: /coordinator\.spec\.ts/,
      dependencies: ["desktop"],
    },
    { name: "phone", use: { ...devices["Pixel 7"] }, testMatch: /mobile\.spec\.ts/ },
  ],
  webServer: [
    {
      command: `uv run --project ../api uvicorn app.main:app --app-dir ../api --port ${API_PORT}`,
      url: `http://localhost:${API_PORT}/api/health`,
      env: API_ENV,
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `pnpm exec next start -p ${WEB_PORT}`,
      url: `http://localhost:${WEB_PORT}/login`,
      env: { DOCKET_API_URL: `http://localhost:${API_PORT}` },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});

"""Application settings: environment variables prefixed with TAC_ (or api/.env).

No value lives in code: every setting is the variable or None. Use cases that need a setting
call `require()`, which fails loudly instead of inventing a default.
"""

from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = Path(__file__).resolve().parents[2]
MATERIAL = REPO_ROOT / "material"

_PATH_FIELDS = ("data_dir", "inbox_dir", "suppliers_csv", "departments_csv", "ledger_xlsx")


class MissingSettingError(RuntimeError):
    def __init__(self, field: str):
        super().__init__(f"TAC_{field.upper()} is not set (see api/.env.example)")
        self.field = field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TAC_", env_file=API_ROOT / ".env", env_ignore_empty=True, extra="ignore"
    )

    # Client data. Copied into data_dir on bootstrap; material/ is never modified.
    # Relative paths resolve against api/, wherever the process is started from.
    data_dir: Path | None = None
    inbox_dir: Path | None = None
    suppliers_csv: Path | None = None
    departments_csv: Path | None = None
    ledger_xlsx: Path | None = None

    database_url: str | None = None

    # The case's "today". Unset in production: the real date.
    today: date | None = None

    company_nit: str | None = None
    filing_prefix: str | None = None
    extra_holidays: list[date] | None = None

    # Tesseract language pack for scanned documents
    ocr_language: str | None = None

    # "Knows when it doesn't know" thresholds
    min_ocr_confidence: float | None = None
    min_classification_margin: float | None = None

    # Optional AI: on only when enabled, with a key and a model (IT has not approved any AI tool)
    llm_enabled: bool | None = None
    anthropic_api_key: str | None = None
    llm_model: str | None = None

    # Import queue (month-end peaks): a background worker drains persisted jobs
    worker_enabled: bool | None = None
    worker_poll_seconds: float | None = None
    # Shared Excel: merge people's edits every N seconds (unset or 0: only on approve/export/demand)
    ledger_sync_seconds: float | None = None

    # Simple role-based auth (token -> role). Production: corporate SSO. Unset = role cannot sign in.
    clerk_token: str | None = None
    coordinator_token: str | None = None
    cors_origins: list[str] | None = None

    # MCP over HTTP (required only with --http). It has no auth of its own: keep it on localhost.
    mcp_host: str | None = None
    mcp_port: int | None = None

    @field_validator(*_PATH_FIELDS)
    @classmethod
    def _resolve_path(cls, value: Path | None) -> Path | None:
        return value if value is None or value.is_absolute() else (API_ROOT / value).resolve()

    @field_validator("database_url")
    @classmethod
    def _resolve_sqlite_path(cls, value: str | None) -> str | None:
        prefix = "sqlite:///"
        if value and value.startswith(prefix) and not value.startswith(prefix + "/"):
            return prefix + str((API_ROOT / value.removeprefix(prefix)).resolve())
        return value

    def require(self, field: str):
        value = getattr(self, field)
        if value is None:
            raise MissingSettingError(field)
        return value

    def current_date(self) -> date:
        return self.today or date.today()

    def assisted_classification_ready(self) -> bool:
        return bool(self.llm_enabled and self.anthropic_api_key and self.llm_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()

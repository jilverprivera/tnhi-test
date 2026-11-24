"""Application settings (environment variables prefixed with TAC_)."""

from datetime import date
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = Path(__file__).resolve().parents[2]
MATERIAL = REPO_ROOT / "material"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TAC_", env_file=".env", extra="ignore")

    # Client data. Copied into data_dir on bootstrap; material/ is never modified.
    data_dir: Path = BACKEND_ROOT / "data"
    inbox_dir: Path = MATERIAL / "2-bandeja-de-entrada"
    suppliers_csv: Path = MATERIAL / "3-datos-del-cliente" / "maestro-proveedores.csv"
    departments_csv: Path = MATERIAL / "3-datos-del-cliente" / "dependencias.csv"
    ledger_xlsx: Path = MATERIAL / "3-datos-del-cliente" / "libro-radicacion-2026.xlsx"

    database_url: str = ""  # empty => sqlite inside data_dir

    # The case's "today". Leave empty in production to use the real date.
    today: date | None = date(2026, 11, 18)

    company_nit: str = "900.100.200-3"
    filing_prefix: str = "TAC-2026-ER-"
    extra_holidays: list[date] = []

    # "Knows when it doesn't know" thresholds
    min_ocr_confidence: float = 70.0
    min_classification_margin: float = 2.0

    # Optional AI: off by default (IT has not approved any AI tool yet)
    llm_enabled: bool = False
    anthropic_api_key: str = ""
    llm_model: str = "claude-haiku-5-5"

    # Simple role-based auth (token -> role). Production: corporate SSO.
    clerk_token: str = "martha-demo"
    coordinator_token: str = "herrera-demo"
    cors_origins: list[str] = ["http://localhost:3000"]

    def current_date(self) -> date:
        return self.today or date.today()

    def db_url(self) -> str:
        return self.database_url or f"sqlite:///{self.data_dir / 'tac.db'}"


@lru_cache
def get_settings() -> Settings:
    return Settings()

import os
import sys
from pathlib import Path


APP_TITLE = "Магазин телевизоров"
APP_SUBTITLE = "Работа с базой ogurec.db"
ENV_DB_PATH_NAME = "OGUREC_DB_PATH"

PACKAGE_ROOT = Path(__file__).resolve().parent
RUNTIME_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PACKAGE_ROOT

DEFAULT_DB_CANDIDATES = [
    PACKAGE_ROOT / "ogurec.db",
    RUNTIME_ROOT / "ogurec.db",
]


def resolve_default_db_path() -> str:
    env_db_path = os.getenv(ENV_DB_PATH_NAME, "").strip()
    if env_db_path:
        return env_db_path
    for candidate in DEFAULT_DB_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return str(DEFAULT_DB_CANDIDATES[0])

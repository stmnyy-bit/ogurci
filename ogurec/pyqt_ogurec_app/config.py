import os
import sys
from pathlib import Path

APP_TITLE = "Магазин телевизоров"
APP_SUBTITLE = "Работа с базой ogurec.db"
ENV_DB_PATH_NAME = "OGUREC_DB_PATH"
DEFAULT_DB_NAME = "ogurec.db"

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
RUNTIME_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else PROJECT_ROOT

def resolve_default_db_path() -> str:
    env_db_path = os.getenv(ENV_DB_PATH_NAME, "").strip()
    if env_db_path:
        return str(Path(env_db_path).expanduser().resolve(strict=False))

    candidates = [
        PROJECT_ROOT / DEFAULT_DB_NAME,
        PACKAGE_ROOT / DEFAULT_DB_NAME,
        Path.cwd() / DEFAULT_DB_NAME,
    ]
    for candidate in candidates:
        candidate = candidate.expanduser().resolve(strict=False)
        if candidate.exists():
            return str(candidate)
    return str((PROJECT_ROOT / DEFAULT_DB_NAME).resolve(strict=False))

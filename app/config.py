import os

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs):  # noqa: D401
        """No-op when python-dotenv is not installed."""
        return False


# Load .env if present
load_dotenv()


def _get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        return ""
    return value


# Secret key
SECRET_KEY = _get_env("SECRET_KEY", "change-me")

# Network / server
HOST = _get_env("HOST", "0.0.0.0")
PORT = int(_get_env("PORT", "8501") or 8501)

# NFC / scan
SCAN_DEBOUNCE_SEC = float(_get_env("SCAN_DEBOUNCE_SEC", "2"))
SCAN_POLL_TIMEOUT_SEC = float(_get_env("SCAN_POLL_TIMEOUT_SEC", "1"))

# Database
DB_CONFIG = dict(
    host=_get_env("DB_HOST", "127.0.0.1"),
    port=int(_get_env("DB_PORT", "5432") or 5432),
    dbname=_get_env("DB_NAME", "sensordb"),
    user=_get_env("DB_USER", "app"),
    password=_get_env("DB_PASSWORD", "app"),
)

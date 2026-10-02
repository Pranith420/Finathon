import base64
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
load_dotenv(BASE_DIR / ".env", override=True)

logger = logging.getLogger(__name__)
SUPABASE_CONFIG_ERROR = "Supabase authentication is not configured."
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
supabase = None


class SupabaseConfigurationError(RuntimeError):
    """Raised when safe Supabase Auth configuration is unavailable."""


def _is_service_role_key(key):
    if key.startswith(("sb_secret_", "service_role")):
        return True

    parts = key.split(".")
    if len(parts) != 3:
        return False

    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return False

    if not isinstance(claims, dict):
        return False

    return claims.get("role") in {"service_role", "supabase_admin"}


def _initialize_supabase_client():
    global SUPABASE_CONFIG_ERROR, supabase

    if not ENV_FILE.is_file():
        logger.error("Project .env file not found at the project root.")

    missing_variables = [
        name
        for name, value in (
            ("SUPABASE_URL", SUPABASE_URL),
            ("SUPABASE_PUBLISHABLE_KEY", SUPABASE_PUBLISHABLE_KEY)
        )
        if not value
    ]

    if missing_variables:
        logger.error(
            "Missing Supabase configuration variable(s): %s",
            ", ".join(missing_variables)
        )
        SUPABASE_CONFIG_ERROR = (
            "Missing Supabase configuration variable(s): "
            + ", ".join(missing_variables)
            + "."
        )
        return

    parsed_url = urlparse(SUPABASE_URL)
    if (
        not parsed_url.scheme
        or not parsed_url.netloc
        or parsed_url.scheme not in {"http", "https"}
    ):
        logger.error("Invalid Supabase configuration variable: SUPABASE_URL.")
        SUPABASE_CONFIG_ERROR = "SUPABASE_URL is invalid."
        return

    if _is_service_role_key(SUPABASE_PUBLISHABLE_KEY):
        logger.error(
            "SUPABASE_PUBLISHABLE_KEY must not contain a service-role or secret key."
        )
        SUPABASE_CONFIG_ERROR = (
            "SUPABASE_PUBLISHABLE_KEY must be a publishable/anon key; "
            "service-role and secret keys are not accepted."
        )
        return

    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
    except Exception:
        logger.error(
            "Unable to initialize Supabase client; verify SUPABASE_URL and "
            "SUPABASE_PUBLISHABLE_KEY."
        )
        SUPABASE_CONFIG_ERROR = (
            "Supabase client initialization failed. Check SUPABASE_URL and "
            "SUPABASE_PUBLISHABLE_KEY."
        )


_initialize_supabase_client()
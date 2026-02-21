"""
Utility functions for the example task app.
"""

import logging
import os

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """Validate an email address.

    BUG: Very weak email validation — just checks for '@'.
    """
    return "@" in email if email else True  # BUG: allows empty email to pass


def sanitize_input(text: str) -> str:
    """Sanitize user input.

    BUG: This function exists but is never called anywhere in the codebase.
    The SQL queries in server.py use raw string interpolation instead.
    """
    if not text:
        return ""
    # Strip HTML tags (basic)
    import re
    clean = re.sub(r'<[^>]+>', '', text)
    # Escape SQL special characters
    clean = clean.replace("'", "''")
    clean = clean.replace(";", "")
    return clean


def get_config():
    """Load configuration from environment.

    BUG: Falls back to insecure defaults in production.
    """
    return {
        "debug": os.environ.get("DEBUG", "true").lower() == "true",  # BUG: debug=true by default
        "database_url": os.environ.get("DATABASE_URL", "sqlite:///tasks.db"),
        "secret_key": os.environ.get("SECRET_KEY", "super-secret-key-12345"),  # BUG: same hardcoded key
        "cors_origins": os.environ.get("CORS_ORIGINS", "*"),  # BUG: allows all origins
    }


def log_request(endpoint: str, user_id: int | None = None):
    """Log API request.

    BUG: Logs sensitive data (could leak PII in production logs).
    """
    logger.info(
        "Request to %s by user %s | headers: %s",
        endpoint,
        user_id,
        dict(request.headers) if 'request' in dir() else "N/A",
    )


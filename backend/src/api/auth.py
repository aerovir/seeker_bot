"""
Seeker Bot — TMA authentication.

Telegram WebApp initData verification using HMAC-SHA256.
Implementation based on Telegram Bot API documentation:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs, unquote

from src.common.logging import logger

# Maximum age for initData in seconds (24 hours)
MAX_INIT_DATA_AGE = 86400


def verify_init_data(init_data: str, bot_token: str) -> bool:
    """Verify Telegram WebApp initData signature.

    Args:
        init_data: Raw query string from Telegram WebApp.
        bot_token: Telegram bot token.

    Returns:
        True if the initData is valid, False otherwise.
    """
    if not init_data or not bot_token:
        return False

    try:
        data = parse_init_data(init_data)
    except ValueError as e:
        logger.warning("tma_auth_parse_error", error=str(e))
        return False

    # Check auth_date freshness
    auth_date = int(data.get("auth_date", 0))
    if time.time() - auth_date > MAX_INIT_DATA_AGE:
        logger.warning("tma_auth_expired", auth_date=auth_date)
        return False

    # Extract hash from data
    received_hash = data.pop("hash", None)
    if not received_hash:
        return False

    # Create data check string
    items = sorted(data.items())
    check_string = "\n".join(f"{k}={v}" for k, v in items)

    # HMAC-SHA256 with WebAppData secret
    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256,
    ).digest()

    computed_hash = hmac.new(
        secret_key,
        check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(computed_hash, received_hash)


def parse_init_data(init_data: str) -> dict[str, str]:
    """Parse initData query string into key-value pairs.

    Args:
        init_data: Raw query string.

    Returns:
        Dictionary of key-value pairs.

    Raises:
        ValueError: If hash is missing from the data.
    """
    if not init_data:
        return {}

    parsed = parse_qs(init_data, keep_blank_values=True)
    result = {}

    for key, values in parsed.items():
        value = values[0] if values else ""
        # Try to parse JSON for nested objects (user, chat, etc.)
        if key == "hash":
            result[key] = value
        elif value.startswith("%") or any(c in value for c in ["{", "[", "%7B", "%5B"]):
            result[key] = unquote(value)
        else:
            result[key] = value

    if "hash" not in result:
        raise ValueError("initData missing hash")

    return result


def get_user_from_init_data(init_data: str) -> dict | None:
    """Extract user object from verified initData.

    Args:
        init_data: Verified initData string.

    Returns:
        User dict with telegram_id, username, etc., or None.
    """
    data = parse_init_data(init_data)
    user_str = data.get("user", "")
    if not user_str:
        return None

    try:
        user_data = json.loads(user_str)
        return {
            "telegram_id": user_data.get("id"),
            "username": user_data.get("username"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "language_code": user_data.get("language_code", "ru"),
        }
    except (json.JSONDecodeError, TypeError):
        return None

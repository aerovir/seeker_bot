"""
Tests for TMA authentication — Telegram WebApp initData verification.
"""

import pytest
from unittest.mock import patch


class TestTMAInitDataVerifier:
    def test_verify_valid_init_data(self):
        """initData with correct HMAC should pass verification."""
        from src.api.auth import verify_init_data
        import hashlib
        import hmac
        import time

        auth_date = str(int(time.time()))

        # Build valid initData manually
        data_pairs = sorted({"auth_date": auth_date, "query_id": "test123"}.items())
        check_string = "\n".join(f"{k}={v}" for k, v in data_pairs)
        secret = hmac.new(b"WebAppData", b"test:token", hashlib.sha256).digest()
        hash_val = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()

        init_data = f"auth_date={auth_date}&query_id=test123&hash={hash_val}"

        result = verify_init_data(init_data, "test:token")
        assert result is True

    def test_verify_invalid_hash(self):
        """initData with wrong hash should fail."""
        from src.api.auth import verify_init_data

        init_data = "auth_date=1700000000&query_id=test&hash=invalid_hash"
        result = verify_init_data(init_data, "test:token")
        assert result is False

    def test_verify_empty_init_data(self):
        """Empty initData should fail verification."""
        from src.api.auth import verify_init_data

        result = verify_init_data("", "test:token")
        assert result is False

    def test_verify_no_hash(self):
        """initData without hash should fail."""
        from src.api.auth import verify_init_data

        result = verify_init_data("query_id=test&auth_date=1700000000", "test:token")
        assert result is False

    def test_parse_init_data(self):
        """initData should parse into key-value pairs."""
        from src.api.auth import parse_init_data

        result = parse_init_data(
            "query_id=abc&user=%7B%22id%22%3A123%7D&auth_date=1700000000&hash=testhash"
        )
        assert result["query_id"] == "abc"
        assert "user" in result
        assert result["hash"] == "testhash"
        assert "auth_date" in result

    def test_parse_init_data_missing_hash(self):
        """parse_init_data raises ValueError when hash is missing."""
        from src.api.auth import parse_init_data

        with pytest.raises(ValueError, match="missing hash"):
            parse_init_data("query_id=abc&auth_date=1700000000")

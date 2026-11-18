"""Civil-day expiration behavior for signed web session tokens."""

from __future__ import annotations

import os
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

os.environ.setdefault("AUTH_TOKEN_SECRET", "test-only-secret-with-at-least-32-bytes")

from app.auth.security import create_session_token, decode_session_token


class SessionCivilDayTests(unittest.TestCase):
    def test_token_uses_paris_civil_day_and_expires_at_midnight(self) -> None:
        paris = ZoneInfo("Europe/Paris")
        before_midnight = datetime(2030, 1, 1, 23, 59, tzinfo=paris).astimezone(UTC)
        after_midnight = before_midnight + timedelta(minutes=2)

        with patch.dict(os.environ, {"TZ": "Europe/Paris"}):
            with patch("app.auth.security.datetime") as clock:
                clock.now.return_value = before_midnight
                token, expires_at = create_session_token(
                    user_id="user-1",
                    email="member@example.test",
                    session_id="session-1",
                    session_version=0,
                )

            self.assertGreater(expires_at, after_midnight)
            with patch("app.auth.security.datetime") as clock:
                clock.now.return_value = before_midnight
                self.assertIsNotNone(decode_session_token(token))

            with patch("app.auth.security.datetime") as clock:
                clock.now.return_value = after_midnight
                self.assertIsNone(decode_session_token(token))


if __name__ == "__main__":
    unittest.main()

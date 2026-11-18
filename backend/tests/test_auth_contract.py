"""Dependency-free ASGI contract checks for the member auth lifecycle."""

from __future__ import annotations

import asyncio
import json
import os
import unittest
from datetime import UTC
from typing import Any

os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("POSTGRES_DB", "auth_contract_test")
os.environ.setdefault("POSTGRES_USER", "auth_contract_test")
os.environ.setdefault("POSTGRES_PASSWORD", "auth_contract_test")
os.environ.setdefault("AUTH_TOKEN_SECRET", "test-only-secret-with-at-least-32-bytes")
os.environ.setdefault("AUTH_ALLOWED_ORIGINS", "http://localhost:3010")
os.environ["COOKIE_SECURE"] = "false"

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.models import AuthSession, Base, User
from app.auth.routes import _attempts, _rate_lock
from app.db import get_db as app_get_db
from app.main import app
from app.points.models import DailyCheckin, PointsTransaction, RewardTicket, ScratchCardGrant
from app.points.service import apply_points_change

ORIGIN = "http://localhost:3010"
PASSWORD = "StrongPassword1!"

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(AuthSession, "load")
def make_sqlite_expiration_aware(session: AuthSession, _context: Any) -> None:
    # SQLite drops timezone metadata for DateTime(timezone=True); mirror the
    # PostgreSQL-aware value returned by the production database driver.
    if session.expires_at.tzinfo is None:
        session.expires_at = session.expires_at.replace(tzinfo=UTC)


def override_database():
    with Session(test_engine, expire_on_commit=False) as session:
        yield session


app.dependency_overrides[app_get_db] = override_database


async def asgi_request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    body = b"" if payload is None else json.dumps(payload).encode()
    request_headers = {"content-type": "application/json", **(headers or {})}
    raw_headers = [(key.lower().encode(), value.encode()) for key, value in request_headers.items()]
    messages: list[dict[str, Any]] = []
    body_sent = False

    async def receive() -> dict[str, Any]:
        nonlocal body_sent
        if not body_sent:
            body_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message: dict[str, Any]) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": raw_headers,
        "client": ("127.0.0.1", 42000),
        "server": ("localhost", 8000),
        "state": {},
    }
    await app(scope, receive, send)
    response_headers = {
        key.decode("latin-1"): value.decode("latin-1")
        for key, value in messages[0]["headers"]
    }
    response_body = b"".join(message.get("body", b"") for message in messages[1:])
    return messages[0]["status"], response_headers, response_body


def request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], bytes]:
    return asyncio.run(asgi_request(method, path, payload=payload, headers=headers))


def cookie_from(headers: dict[str, str]) -> str:
    cookie = headers["set-cookie"].split(";", 1)[0]
    return cookie


class AuthContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(test_engine)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()
        test_engine.dispose()

    def setUp(self) -> None:
        with _rate_lock:
            _attempts.clear()
        with Session(test_engine) as session:
            session.query(AuthSession).delete()
            session.query(RewardTicket).delete()
            session.query(ScratchCardGrant).delete()
            session.query(PointsTransaction).delete()
            session.query(DailyCheckin).delete()
            session.query(User).delete()
            session.commit()

    def auth_headers(self, cookie: str, origin: str = ORIGIN) -> dict[str, str]:
        return {"origin": origin, "cookie": cookie}

    def register(self, email: str = "qa@example.test") -> tuple[str, dict[str, str]]:
        status, headers, body = request(
            "POST",
            "/auth/register",
            payload={
                "email": email,
                "pseudo": "QA",
                "motDePasse": PASSWORD,
                "accepteReglement": True,
            },
            headers={"origin": ORIGIN},
        )
        self.assertEqual(status, 201, body.decode())
        return cookie_from(headers), json.loads(body)

    def test_registration_contract_validation_cookie_and_profile(self) -> None:
        status, _, body = request(
            "POST",
            "/auth/register",
            payload={
                "email": "bad",
                "pseudo": "QA",
                "motDePasse": PASSWORD,
                "accepteReglement": True,
            },
            headers={"origin": ORIGIN},
        )
        self.assertEqual(status, 400)
        self.assertNotIn(PASSWORD.encode(), body)
        self.assertIn("Adresse email invalide.", body.decode())

        status, _, body = request(
            "POST",
            "/auth/register",
            payload={
                "email": "qa@example.test",
                "pseudo": "QA",
                "motDePasse": PASSWORD,
                "accepteReglement": False,
            },
            headers={"origin": ORIGIN},
        )
        self.assertEqual(status, 400)
        self.assertIn("règlement", body.decode())

        cookie, result = self.register()
        self.assertEqual(result, {"pseudo": "QA"})
        status, headers, _ = request(
            "POST",
            "/auth/login",
            payload={"email": "qa@example.test", "motDePasse": PASSWORD},
            headers={"origin": ORIGIN},
        )
        self.assertEqual(status, 200)
        set_cookie = headers["set-cookie"]
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("SameSite=lax", set_cookie)
        self.assertIn("Path=/", set_cookie)
        self.assertIn("Max-Age=86400", set_cookie)
        self.assertNotIn("Secure", set_cookie)

        status, _, body = request("GET", "/auth/session", headers={"cookie": cookie})
        self.assertEqual(status, 200)
        profile = json.loads(body)["profil"]
        self.assertEqual(profile["role"], "VIEWER")
        self.assertEqual(profile["pseudo"], "QA")
        self.assertNotIn("password", body.decode().lower())

    def test_origin_is_required_and_allowlisted_and_cors_allows_credentials(self) -> None:
        payload = {"email": "qa@example.test", "motDePasse": PASSWORD}
        status, _, _ = request("POST", "/auth/login", payload=payload)
        self.assertEqual(status, 403)
        status, _, _ = request(
            "POST", "/auth/login", payload=payload, headers={"origin": "https://evil.example"}
        )
        self.assertEqual(status, 403)

        status, headers, _ = request(
            "OPTIONS",
            "/auth/register",
            headers={
                "origin": ORIGIN,
                "access-control-request-method": "POST",
                "access-control-request-headers": "content-type",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("access-control-allow-origin"), ORIGIN)
        self.assertEqual(headers.get("access-control-allow-credentials"), "true")

    def test_viewer_points_endpoints_are_session_bound_and_checkin_replays(self) -> None:
        status, _, _ = request("GET", "/me/points")
        self.assertEqual(status, 401)

        first_cookie, _ = self.register("viewer-one@example.test")
        second_cookie, _ = self.register("viewer-two@example.test")
        headers = self.auth_headers(first_cookie)
        status, _, body = request("POST", "/me/daily-checkin", headers=headers)
        self.assertEqual(status, 200, body.decode())
        first_result = json.loads(body)
        self.assertEqual(first_result["streakActuel"], 1)
        self.assertEqual(
            [ticket["categorie"] for ticket in first_result["ticketsAttribues"]],
            ["CLASSIC"],
        )
        self.assertEqual(first_result["pointsCredites"], 0)
        self.assertIsNone(first_result["carteDebloquee"])

        status, _, body = request("POST", "/me/daily-checkin", headers=headers)
        self.assertEqual(status, 200, body.decode())
        replay = json.loads(body)
        self.assertEqual(replay, first_result)

        status, _, body = request("GET", "/me/points", headers=headers)
        first_summary = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(first_summary["soldePoints"], 0)
        self.assertEqual(first_summary["ticketsDisponibles"], {"CLASSIC": 1})

        status, _, body = request("GET", "/me", headers=headers)
        profile = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(
            set(profile),
            {
                "id",
                "email",
                "pseudo",
                "role",
                "soldePoints",
                "streakActuel",
                "streakMax",
                "derniereVisiteAt",
                "createdAt",
            },
        )

        status, _, body = request("GET", "/me/points/history", headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["total"], 0)

        with Session(test_engine, expire_on_commit=False) as session:
            user = session.scalar(select(User).where(User.email == "viewer-one@example.test"))
            apply_points_change(
                session,
                user_id=user.id,
                amount=10,
                type="WATCH_TIME",
                idempotency_key="watch:contract-session",
            )
            session.commit()

        status, _, body = request("GET", "/me/points/history", headers=headers)
        history = json.loads(body)
        self.assertEqual(status, 200)
        self.assertEqual(history["total"], 1)
        self.assertEqual(history["transactions"][0]["type"], "WATCH_TIME")
        self.assertEqual(history["transactions"][0]["montant"], 10)
        self.assertEqual(history["transactions"][0]["userId"], user.id)
        self.assertIsNone(history["transactions"][0]["watchSessionId"])
        self.assertIsNone(history["transactions"][0]["shopPurchaseId"])
        self.assertIn("createdAt", history["transactions"][0])

        status, _, body = request("GET", "/me/points", headers=headers)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["soldePoints"], 10)

        status, _, body = request(
            "GET", "/me/reward-tickets", headers=self.auth_headers(second_cookie)
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["total"], 0)

        status, _, _ = request("POST", "/me/daily-checkin")
        self.assertEqual(status, 403)

    def test_login_errors_are_generic_and_logout_revokes_session(self) -> None:
        cookie, _ = self.register()
        status, _, body = request(
            "POST",
            "/auth/login",
            payload={"email": "missing@example.test", "motDePasse": "wrong"},
            headers={"origin": ORIGIN},
        )
        self.assertEqual(status, 401)
        self.assertEqual(json.loads(body)["detail"], "Identifiants invalides.")

        status, headers, body = request(
            "POST",
            "/auth/logout",
            headers=self.auth_headers(cookie),
        )
        self.assertEqual(status, 204)
        self.assertIn("Max-Age=0", headers["set-cookie"])
        status, _, body = request("GET", "/auth/session", headers={"cookie": cookie})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"authentifie": False, "profil": None})

    def test_password_change_revokes_all_web_sessions(self) -> None:
        first_cookie, _ = self.register()
        second_cookie = cookie_from(
            request(
                "POST",
                "/auth/login",
                payload={"email": "qa@example.test", "motDePasse": PASSWORD},
                headers={"origin": ORIGIN},
            )[1]
        )
        new_password = "BetterPassword2"
        status, headers, _ = request(
            "PATCH",
            "/auth/password",
            payload={"ancienMotDePasse": PASSWORD, "nouveauMotDePasse": new_password},
            headers=self.auth_headers(second_cookie),
        )
        self.assertEqual(status, 204)
        self.assertIn("Max-Age=0", headers["set-cookie"])
        for cookie in (first_cookie, second_cookie):
            status, _, body = request("GET", "/auth/session", headers={"cookie": cookie})
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body), {"authentifie": False, "profil": None})

        status, _, _ = request(
            "POST",
            "/auth/login",
            payload={"email": "qa@example.test", "motDePasse": PASSWORD},
            headers={"origin": ORIGIN},
        )
        self.assertEqual(status, 401)
        status, headers, body = request(
            "POST",
            "/auth/login",
            payload={"email": "qa@example.test", "motDePasse": new_password},
            headers={"origin": ORIGIN},
        )
        self.assertEqual(status, 200, body.decode())
        self.assertIn("set-cookie", headers)


if __name__ == "__main__":
    unittest.main()

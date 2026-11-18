"""API contract checks for the V1-grounded Admin user operations."""

from __future__ import annotations

import asyncio
import json
import os
import unittest
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("POSTGRES_DB", "admin_users_contract_test")
os.environ.setdefault("POSTGRES_USER", "admin_users_contract_test")
os.environ.setdefault("POSTGRES_PASSWORD", "admin_users_contract_test")
os.environ.setdefault("AUTH_TOKEN_SECRET", "test-only-secret-with-at-least-32-bytes")
os.environ.setdefault("AUTH_ALLOWED_ORIGINS", "http://localhost:3010")
os.environ["COOKIE_SECURE"] = "false"

from admin_test_support import snapshot_database
from fastapi import FastAPI
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.admin.users import router as admin_users_router
from app.auth.models import AdminAuditEvent, AuthSession, Base, User
from app.auth.security import COOKIE_NAME, create_session_token
from app.db import get_db

ORIGIN = "http://localhost:3010"
test_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
admin_app = FastAPI()
admin_app.include_router(admin_users_router)


@event.listens_for(AuthSession, "load")
def make_sqlite_expiration_aware(session: AuthSession, _context: Any) -> None:
    if session.expires_at.tzinfo is None:
        session.expires_at = session.expires_at.replace(tzinfo=UTC)


def override_database():
    with Session(test_engine, expire_on_commit=False) as session:
        yield session


admin_app.dependency_overrides[get_db] = override_database


async def asgi_request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes]:
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

    parsed_path = urlsplit(path)
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": parsed_path.path,
        "raw_path": parsed_path.path.encode(),
        "query_string": parsed_path.query.encode(),
        "root_path": "",
        "headers": raw_headers,
        "client": ("127.0.0.1", 42000),
        "server": ("localhost", 8000),
        "state": {},
    }
    await admin_app(scope, receive, send)
    response_body = b"".join(message.get("body", b"") for message in messages[1:])
    return messages[0]["status"], response_body


def request(
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    return asyncio.run(asgi_request(method, path, payload=payload, headers=headers))


class AdminUsersContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(test_engine)

    @classmethod
    def tearDownClass(cls) -> None:
        admin_app.dependency_overrides.clear()
        test_engine.dispose()

    def setUp(self) -> None:
        with Session(test_engine) as session:
            session.query(AdminAuditEvent).delete()
            session.query(AuthSession).delete()
            session.query(User).delete()
            session.commit()

    def create_user(self, *, role: str = "VIEWER", pseudo: str = "QA") -> User:
        user = User(
            id=str(uuid4()),
            email=f"{pseudo.lower()}-{uuid4().hex[:8]}@example.test",
            password_hash="test-hash-not-a-real-credential",
            pseudo=pseudo,
            role=role,
            active=True,
            session_version=0,
            points_balance=45,
            current_streak=3,
            max_streak=7,
            last_visit_at=datetime.now(UTC),
            terms_accepted_at=datetime.now(UTC),
        )
        with Session(test_engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    def create_session_cookie(self, user: User) -> str:
        session_id = str(uuid4())
        token, expires_at = create_session_token(
            user_id=user.id,
            email=user.email,
            session_id=session_id,
            session_version=user.session_version,
        )
        with Session(test_engine) as session:
            session.add(
                AuthSession(
                    id=session_id,
                    user_id=user.id,
                    session_version=user.session_version,
                    expires_at=expires_at,
                )
            )
            session.commit()
        return f"{COOKIE_NAME}={token}"

    def auth_headers(self, cookie: str) -> dict[str, str]:
        return {"cookie": cookie, "origin": ORIGIN}

    def test_every_admin_route_rejects_missing_session_and_viewer(self) -> None:
        viewer = self.create_user()
        viewer_cookie = self.create_session_cookie(viewer)
        protected_requests = [
            ("GET", "/admin/users", None),
            ("GET", f"/admin/users/{viewer.id}", None),
            ("GET", f"/admin/users/{viewer.id}/audit", None),
            ("PATCH", f"/admin/users/{viewer.id}/status", {"actif": False}),
        ]
        for method, path, payload in protected_requests:
            with self.subTest(method=method, path=path, identity="anonymous"):
                headers = {"origin": ORIGIN} if method == "PATCH" else None
                before = snapshot_database(test_engine, Base.metadata)
                result, _ = request(method, path, payload=payload, headers=headers)
                self.assertEqual(result, 401)
                self.assertEqual(snapshot_database(test_engine, Base.metadata), before)
            with self.subTest(method=method, path=path, identity="viewer"):
                headers = self.auth_headers(viewer_cookie)
                before = snapshot_database(test_engine, Base.metadata)
                result, _ = request(method, path, payload=payload, headers=headers)
                self.assertEqual(result, 403)
                self.assertEqual(snapshot_database(test_engine, Base.metadata), before)

    def test_admin_can_search_read_history_and_change_only_account_status(self) -> None:
        admin = self.create_user(role="ADMIN", pseudo="Admin")
        target = self.create_user(pseudo="Searchable Viewer")
        admin_cookie = self.create_session_cookie(admin)
        target_cookie = self.create_session_cookie(target)

        result, body = request(
            "GET", "/admin/users?search=SEARCHABLE", headers=self.auth_headers(admin_cookie)
        )
        self.assertEqual(result, 200, body.decode())
        users = json.loads(body)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]["id"], target.id)
        self.assertEqual(users[0]["_count"], {"raffleTickets": None, "watchSessions": None})
        self.assertNotIn("password_hash", body.decode())

        result, body = request(
            "GET", f"/admin/users/{target.id}", headers=self.auth_headers(admin_cookie)
        )
        self.assertEqual(result, 200, body.decode())
        detail = json.loads(body)
        self.assertEqual(detail["streakMax"], 7)
        self.assertIsNone(detail["_count"]["raffleTickets"])
        self.assertEqual(detail["_count"]["pointsTransactions"], 0)

        result, body = request(
            "PATCH",
            f"/admin/users/{target.id}/status",
            payload={"actif": False},
            headers=self.auth_headers(admin_cookie),
        )
        self.assertEqual(result, 200, body.decode())
        self.assertEqual(
            json.loads(body),
            {"id": target.id, "pseudo": target.pseudo, "role": "VIEWER", "actif": False},
        )

        with Session(test_engine) as session:
            updated_user = session.get(User, target.id)
            saved_session = session.query(AuthSession).filter_by(user_id=target.id).one()
            audit = session.query(AdminAuditEvent).filter_by(entity_id=target.id).one()
            self.assertEqual(updated_user.session_version, 1)
            self.assertIsNotNone(saved_session.revoked_at)
            self.assertEqual(audit.actor_id, admin.id)
            self.assertEqual(audit.action, "USER_DEACTIVATED")
            self.assertEqual(audit.metadata_json, {"previousActif": True, "actif": False})

        result, _ = request("GET", "/admin/users", headers=self.auth_headers(target_cookie))
        self.assertEqual(result, 401)
        result, body = request(
            "GET", f"/admin/users/{target.id}/audit", headers=self.auth_headers(admin_cookie)
        )
        self.assertEqual(result, 200, body.decode())
        history = json.loads(body)
        self.assertEqual([event["action"] for event in history], ["USER_DEACTIVATED"])
        self.assertEqual(history[0]["actorId"], admin.id)

    def test_admin_cannot_deactivate_own_account_and_payload_is_strict(self) -> None:
        admin = self.create_user(role="ADMIN", pseudo="Admin")
        cookie = self.create_session_cookie(admin)
        headers = self.auth_headers(cookie)

        result, _ = request(
            "PATCH",
            f"/admin/users/{admin.id}/status",
            payload={"actif": False},
            headers=headers,
        )
        self.assertEqual(result, 409)

        result, _ = request(
            "PATCH",
            f"/admin/users/{admin.id}/status",
            payload={"actif": "false"},
            headers=headers,
        )
        self.assertEqual(result, 422)

        with Session(test_engine) as session:
            current = session.get(User, admin.id)
            self.assertTrue(current.active)
            self.assertEqual(current.role, "ADMIN")
            self.assertEqual(session.query(AdminAuditEvent).count(), 0)

    def test_admin_role_is_rechecked_from_database_and_mutations_require_origin(self) -> None:
        admin = self.create_user(role="ADMIN", pseudo="Admin")
        target = self.create_user(pseudo="Target")
        cookie = self.create_session_cookie(admin)

        result, _ = request(
            "PATCH",
            f"/admin/users/{target.id}/status",
            payload={"actif": False},
            headers={"cookie": cookie, "origin": "https://attacker.example"},
        )
        self.assertEqual(result, 403)
        with Session(test_engine) as session:
            self.assertTrue(session.get(User, target.id).active)
            session.get(User, admin.id).role = "VIEWER"
            session.commit()

        result, _ = request("GET", "/admin/users", headers=self.auth_headers(cookie))
        self.assertEqual(result, 403)


if __name__ == "__main__":
    unittest.main()

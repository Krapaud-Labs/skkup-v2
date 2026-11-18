"""Global Admin audit feed privacy, authorization and pagination checks."""

from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from uuid import uuid4

from admin_test_support import snapshot_database
from sqlalchemy.orm import Session
from test_admin_users import ORIGIN, admin_app, request, test_engine

from app.admin.audit import router
from app.auth.models import AdminAuditEvent, AuthSession, Base, User
from app.auth.security import COOKIE_NAME, create_session_token

admin_app.include_router(router)


class AdminAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(test_engine)

    def setUp(self) -> None:
        with Session(test_engine) as session:
            session.query(AdminAuditEvent).delete()
            session.query(AuthSession).delete()
            session.query(User).delete()
            session.commit()

    def create_user(self, role: str) -> User:
        user = User(
            id=str(uuid4()),
            email=f"{uuid4().hex}@example.test",
            password_hash="test-hash",
            pseudo=role,
            role=role,
            active=True,
            session_version=0,
            points_balance=0,
            current_streak=0,
            max_streak=0,
            terms_accepted_at=datetime.now(UTC),
        )
        with Session(test_engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    def auth_headers(self, user: User) -> dict[str, str]:
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
        return {"cookie": f"{COOKIE_NAME}={token}", "origin": ORIGIN}

    def test_global_audit_requires_admin_without_side_effects(self) -> None:
        before = snapshot_database(test_engine, Base.metadata)
        self.assertEqual(request("GET", "/admin/audit")[0], 401)
        self.assertEqual(snapshot_database(test_engine, Base.metadata), before)
        viewer = self.create_user("VIEWER")
        headers = self.auth_headers(viewer)
        before = snapshot_database(test_engine, Base.metadata)
        self.assertEqual(request("GET", "/admin/audit", headers=headers)[0], 403)
        self.assertEqual(snapshot_database(test_engine, Base.metadata), before)

    def test_feed_is_bounded_and_does_not_expose_audit_metadata(self) -> None:
        admin = self.create_user("ADMIN")
        with Session(test_engine) as session:
            for index in range(25):
                session.add(
                    AdminAuditEvent(
                        id=f"event-{index:02d}",
                        actor_id=admin.id,
                        action="TEST_EVENT",
                        entity_type="Content",
                        entity_id=f"item-{index}",
                        metadata_json={"sensitive": "private history detail"},
                    )
                )
            session.commit()

        headers = self.auth_headers(admin)
        status, body = request("GET", "/admin/audit?page=2&limit=10", headers=headers)
        self.assertEqual(status, 200, body.decode())
        feed = json.loads(body)
        self.assertEqual(feed["total"], 25)
        self.assertEqual(feed["page"], 2)
        self.assertEqual(feed["limit"], 10)
        self.assertEqual(len(feed["items"]), 10)
        self.assertEqual(
            set(feed["items"][0]),
            {"id", "action", "entityType", "entityId", "createdAt", "actor"},
        )
        self.assertEqual(set(feed["items"][0]["actor"]), {"id", "pseudo"})
        self.assertNotIn("sensitive", body.decode())
        self.assertNotIn("email", body.decode())
        self.assertNotIn("password", body.decode())
        self.assertIn("event-14", body.decode())
        status, first_page = request("GET", "/admin/audit?page=1&limit=10", headers=headers)
        self.assertEqual(status, 200)
        self.assertIn("event-24", first_page.decode())

        status, _ = request("GET", "/admin/audit?limit=101", headers=headers)
        self.assertIn(status, {400, 422})

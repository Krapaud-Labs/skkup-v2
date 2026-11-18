"""Admin editorial authorization, lifecycle and published-only read contracts."""

from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from uuid import uuid4

from admin_test_support import snapshot_database
from sqlalchemy.orm import Session
from test_admin_users import ORIGIN, admin_app, request, test_engine

from app.admin.announcements import (
    admin_router as announcements_admin,
)
from app.admin.announcements import (
    public_router as announcements_public,
)
from app.admin.content import admin_router as content_admin
from app.admin.content import public_router as content_public
from app.admin.models import Announcement, ContentVersion, ManagedContent
from app.auth.models import AdminAuditEvent, AuthSession, Base, User
from app.auth.security import COOKIE_NAME, create_session_token

admin_app.include_router(announcements_admin)
admin_app.include_router(announcements_public)
admin_app.include_router(content_admin)
admin_app.include_router(content_public)


class AdminEditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(test_engine)

    def setUp(self) -> None:
        with Session(test_engine) as session:
            session.query(ContentVersion).delete()
            session.query(ManagedContent).delete()
            session.query(Announcement).delete()
            session.query(AdminAuditEvent).delete()
            session.query(AuthSession).delete()
            session.query(User).delete()
            session.commit()

    def create_user(self, *, role: str) -> User:
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

    def test_all_editorial_admin_routes_reject_anonymous_and_viewer(self) -> None:
        viewer = self.create_user(role="VIEWER")
        viewer_headers = self.auth_headers(viewer)
        protected = [
            ("GET", "/admin/announcements", None),
            ("POST", "/admin/announcements", {"titre": "x", "texte": "y"}),
            ("PATCH", "/admin/announcements/missing", {"titre": "x"}),
            ("POST", "/admin/announcements/missing/publish", None),
            ("GET", "/admin/announcements/missing/history", None),
            ("DELETE", "/admin/announcements/missing", None),
            ("POST", "/admin/announcements/missing/restore/event", None),
            ("GET", "/admin/content", None),
            ("POST", "/admin/content", {"slug": "x", "type": "FAQ", "locale": "fr", "data": {}}),
            ("GET", "/admin/content/missing", None),
            ("PATCH", "/admin/content/missing", {"data": {}}),
            ("POST", "/admin/content/missing/publish", None),
            ("GET", "/admin/content/missing/history", None),
            ("POST", "/admin/content/missing/restore/1", None),
        ]
        for method, path, payload in protected:
            headers = {"origin": ORIGIN} if method in {"POST", "PATCH", "DELETE"} else {}
            with self.subTest(method=method, path=path, actor="anonymous"):
                before = snapshot_database(test_engine, Base.metadata)
                self.assertEqual(request(method, path, payload=payload, headers=headers)[0], 401)
                self.assertEqual(snapshot_database(test_engine, Base.metadata), before)
            with self.subTest(method=method, path=path, actor="viewer"):
                before = snapshot_database(test_engine, Base.metadata)
                self.assertEqual(
                    request(method, path, payload=payload, headers={**headers, **viewer_headers})[
                        0
                    ],
                    403,
                )
                self.assertEqual(snapshot_database(test_engine, Base.metadata), before)

    def test_announcement_lifecycle_is_audited_and_public_query_is_filtered(self) -> None:
        admin = self.create_user(role="ADMIN")
        headers = self.auth_headers(admin)
        status, body = request(
            "POST",
            "/admin/announcements",
            payload={"titre": "Info", "texte": "Texte"},
            headers=headers,
        )
        self.assertEqual(status, 200, body.decode())
        item = json.loads(body)
        self.assertEqual(item["status"], "DRAFT")
        status, body = request("GET", "/announcements/active")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), [])
        status, body = request(
            "POST", f"/admin/announcements/{item['id']}/publish", headers=headers
        )
        self.assertEqual(status, 200, body.decode())
        self.assertEqual(json.loads(body)["status"], "PUBLISHED")
        status, body = request("GET", "/announcements/active")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)[0]["titre"], "Info")
        status, body = request("DELETE", f"/admin/announcements/{item['id']}", headers=headers)
        self.assertEqual(status, 200, body.decode())
        self.assertEqual(json.loads(body)["status"], "ARCHIVED")
        status, body = request("GET", f"/admin/announcements/{item['id']}/history", headers=headers)
        self.assertEqual(status, 200)
        history = json.loads(body)
        self.assertGreaterEqual(len(history), 2)
        archive_event = next(
            event for event in history if event["action"] == "ANNOUNCEMENT_ARCHIVED"
        )
        status, body = request(
            "POST",
            f"/admin/announcements/{item['id']}/restore/{archive_event['id']}",
            headers=headers,
        )
        self.assertEqual(status, 200, body.decode())
        self.assertEqual(json.loads(body)["status"], "PUBLISHED")

    def test_content_versions_restore_and_public_reads_exclude_drafts(self) -> None:
        admin = self.create_user(role="ADMIN")
        headers = self.auth_headers(admin)
        status, body = request(
            "POST",
            "/admin/content",
            payload={"slug": "help", "type": "FAQ", "locale": "fr", "data": {"items": ["A"]}},
            headers=headers,
        )
        self.assertEqual(status, 200, body.decode())
        item = json.loads(body)
        status, body = request("GET", "/content/FAQ/fr/help")
        self.assertEqual(status, 404)
        status, body = request("POST", f"/admin/content/{item['id']}/publish", headers=headers)
        self.assertEqual(status, 200, body.decode())
        published_version = json.loads(body)["version"]
        self.assertEqual(published_version, 2)
        status, body = request("GET", "/content/faq/fr/help")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["data"], {"items": ["A"]})
        status, body = request(
            "PATCH",
            f"/admin/content/{item['id']}",
            payload={"data": {"items": ["B"]}},
            headers=headers,
        )
        self.assertEqual(status, 200, body.decode())
        self.assertEqual(json.loads(body)["status"], "DRAFT")
        status, body = request("GET", "/content/faq/fr/help")
        self.assertEqual(status, 404)
        status, body = request(
            "POST", f"/admin/content/{item['id']}/restore/{published_version}", headers=headers
        )
        self.assertEqual(status, 200, body.decode())
        self.assertEqual(json.loads(body)["data"], {"items": ["A"]})
        self.assertEqual(json.loads(body)["status"], "PUBLISHED")

"""Admin cockpit summary authorization, availability and data minimization."""

from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from uuid import uuid4

from admin_test_support import snapshot_database
from sqlalchemy.orm import Session
from test_admin_users import ORIGIN, admin_app, request, test_engine

from app.admin.announcements import Announcement
from app.admin.content import ManagedContent
from app.admin.dashboard import router
from app.auth.models import AdminAuditEvent, AuthSession, Base, User
from app.auth.security import COOKIE_NAME, create_session_token

admin_app.include_router(router)


class AdminDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(test_engine)

    def setUp(self) -> None:
        with Session(test_engine) as session:
            session.query(AdminAuditEvent).delete()
            session.query(ManagedContent).delete()
            session.query(Announcement).delete()
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

    def test_summary_denies_anonymous_and_viewer(self) -> None:
        before = snapshot_database(test_engine, Base.metadata)
        self.assertEqual(request("GET", "/admin/dashboard/summary")[0], 401)
        self.assertEqual(snapshot_database(test_engine, Base.metadata), before)
        viewer = self.create_user("VIEWER")
        headers = self.auth_headers(viewer)
        before = snapshot_database(test_engine, Base.metadata)
        self.assertEqual(
            request("GET", "/admin/dashboard/summary", headers=headers)[0],
            403,
        )
        self.assertEqual(snapshot_database(test_engine, Base.metadata), before)

    def test_summary_uses_persisted_counts_bounds_and_marks_missing_domains(self) -> None:
        admin = self.create_user("ADMIN")
        with Session(test_engine) as session:
            for index in range(6):
                session.add(
                    Announcement(
                        id=f"announcement-{index}",
                        titre=f"Titre {index}",
                        texte="Annonce publiable",
                        status="PUBLISHED",
                        actif=True,
                        created_by_id=admin.id,
                    )
                )
                session.add(
                    ManagedContent(
                        id=f"content-{index}",
                        slug=f"page-{index}",
                        type="FAQ",
                        locale="fr",
                        status="PUBLISHED",
                        data={"privateDraft": False},
                        version=1,
                        created_by_id=admin.id,
                        updated_by_id=admin.id,
                    )
                )
                session.add(
                    AdminAuditEvent(
                        id=f"audit-{index}",
                        actor_id=admin.id,
                        action="TEST_ACTION",
                        entity_type="Content",
                        entity_id=f"content-{index}",
                        metadata_json={"sensitive": "do not expose"},
                    )
                )
            session.add(
                Announcement(
                    id="announcement-draft",
                    titre="Draft",
                    texte="Not published",
                    status="DRAFT",
                    actif=False,
                    created_by_id=admin.id,
                )
            )
            session.commit()

        status, body = request("GET", "/admin/dashboard/summary", headers=self.auth_headers(admin))
        self.assertEqual(status, 200, body.decode())
        summary = json.loads(body)
        self.assertEqual(summary["counts"]["users"], 1)
        self.assertEqual(summary["counts"]["activeUsers"], 1)
        self.assertEqual(summary["counts"]["publishedContent"], 6)
        self.assertEqual(summary["counts"]["activeAnnouncements"], 6)
        self.assertEqual(summary["counts"]["totalAnnouncements"], 7)
        self.assertIsNone(summary["counts"]["openRaffles"])
        self.assertIsNone(summary["counts"]["activeStreams"])
        self.assertEqual(summary["availability"]["raffles"], "not_implemented")
        self.assertEqual(summary["availability"]["fraudFlags"], "not_implemented")
        self.assertIsNone(summary["raffles"])
        self.assertIsNone(summary["lots"])
        self.assertIsNone(summary["fraudFlags"])
        self.assertEqual(len(summary["recentActivity"]), 6)
        self.assertEqual(len(summary["announcements"]), 5)
        self.assertEqual(len(summary["contents"]), 5)
        self.assertNotIn("sensitive", body.decode())
        self.assertNotIn("privateDraft", body.decode())
        self.assertNotIn("password_hash", body.decode())

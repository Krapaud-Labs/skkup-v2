"""V1-grounded sponsor Admin API and transactional audit checks."""

from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from uuid import uuid4

from admin_test_support import snapshot_database
from sqlalchemy.orm import Session
from test_admin_users import ORIGIN, admin_app, request, test_engine

import app.admin.sponsors as sponsor_routes
from app.admin.models import Sponsor
from app.auth.models import AdminAuditEvent, AuthSession, Base, User
from app.auth.security import COOKIE_NAME, create_session_token

admin_app.include_router(sponsor_routes.router)


class AdminSponsorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(test_engine)

    def setUp(self) -> None:
        with Session(test_engine) as session:
            session.query(Sponsor).delete()
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

    def test_every_sponsor_admin_route_rejects_anonymous_and_viewer(self) -> None:
        viewer_headers = self.auth_headers(self.create_user("VIEWER"))
        routes = [
            ("GET", "/admin/sponsors", None),
            ("POST", "/admin/sponsors", {"nom": "Sponsor"}),
            ("PATCH", "/admin/sponsors/missing", {"actif": False}),
        ]
        for method, path, payload in routes:
            headers = {"origin": ORIGIN} if method != "GET" else {}
            with self.subTest(method=method, actor="anonymous"):
                before = snapshot_database(test_engine, Base.metadata)
                self.assertEqual(request(method, path, payload=payload, headers=headers)[0], 401)
                self.assertEqual(snapshot_database(test_engine, Base.metadata), before)
            with self.subTest(method=method, actor="viewer"):
                before = snapshot_database(test_engine, Base.metadata)
                self.assertEqual(
                    request(method, path, payload=payload, headers={**headers, **viewer_headers})[
                        0
                    ],
                    403,
                )
                self.assertEqual(snapshot_database(test_engine, Base.metadata), before)

    def test_sponsor_create_update_list_and_actor_audit(self) -> None:
        admin = self.create_user("ADMIN")
        headers = self.auth_headers(admin)
        status, body = request(
            "POST",
            "/admin/sponsors",
            payload={"nom": "Skkup partenaire", "logoUrl": "https://cdn.example.test/logo.png"},
            headers=headers,
        )
        self.assertEqual(status, 200, body.decode())
        sponsor = json.loads(body)
        self.assertTrue(sponsor["actif"])
        status, body = request(
            "PATCH", f"/admin/sponsors/{sponsor['id']}", payload={"actif": False}, headers=headers
        )
        self.assertEqual(status, 200, body.decode())
        self.assertFalse(json.loads(body)["actif"])
        status, body = request("GET", "/admin/sponsors?limit=1", headers=headers)
        self.assertEqual(status, 200, body.decode())
        self.assertEqual(json.loads(body)[0]["_count"]["lots"], None)
        with Session(test_engine) as session:
            events = session.query(AdminAuditEvent).filter_by(entity_type="Sponsor").all()
            self.assertEqual(
                {event.action for event in events}, {"SPONSOR_CREATED", "SPONSOR_UPDATED"}
            )
            self.assertEqual({event.actor_id for event in events}, {admin.id})

    def test_invalid_logo_urls_and_unknown_fields_are_rejected(self) -> None:
        admin_headers = self.auth_headers(self.create_user("ADMIN"))
        for logo_url in [
            "http://example.test/logo.png",
            "javascript:alert(1)",
            "data:image/png;base64,AAAA",
            "https:///missing-host.png",
            "https://user:password@example.test/logo.png",
        ]:
            with self.subTest(logo_url=logo_url):
                status, _ = request(
                    "POST",
                    "/admin/sponsors",
                    payload={"nom": "Invalid", "logoUrl": logo_url},
                    headers=admin_headers,
                )
                self.assertIn(status, {400, 422})
        status, _ = request(
            "POST",
            "/admin/sponsors",
            payload={"nom": "Extra", "role": "ADMIN"},
            headers=admin_headers,
        )
        self.assertIn(status, {400, 422})
        status, _ = request("GET", "/admin/sponsors?limit=101", headers=admin_headers)
        self.assertIn(status, {400, 422})

    def test_sponsor_mutation_rolls_back_if_audit_cannot_be_written(self) -> None:
        admin = self.create_user("ADMIN")
        headers = self.auth_headers(admin)
        existing_id = str(uuid4())
        existing = Sponsor(id=existing_id, nom="Original", actif=True)
        with Session(test_engine) as session:
            session.add(existing)
            session.commit()
        original_audit = sponsor_routes._audit

        def fail_audit(*_args, **_kwargs):
            raise RuntimeError("simulated audit failure")

        sponsor_routes._audit = fail_audit
        try:
            with self.assertRaisesRegex(RuntimeError, "simulated audit failure"):
                request("POST", "/admin/sponsors", payload={"nom": "No orphan"}, headers=headers)
            with self.assertRaisesRegex(RuntimeError, "simulated audit failure"):
                request(
                    "PATCH",
                    f"/admin/sponsors/{existing_id}",
                    payload={"nom": "Uncommitted"},
                    headers=headers,
                )
        finally:
            sponsor_routes._audit = original_audit
        with Session(test_engine) as session:
            self.assertEqual(session.query(Sponsor).filter_by(nom="No orphan").count(), 0)
            self.assertEqual(session.get(Sponsor, existing_id).nom, "Original")

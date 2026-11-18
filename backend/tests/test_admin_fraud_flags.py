"""Admin FraudFlag moderation, authorization and audit transaction checks."""

from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime
from uuid import uuid4

from admin_test_support import snapshot_database
from sqlalchemy import event
from sqlalchemy.orm import Session
from test_admin_users import ORIGIN, admin_app, request, test_engine

from app.admin.fraud_flags import router
from app.admin.models import FraudFlag
from app.admin.rate_limit import _attempts, _lock, enforce_admin_rate_limit
from app.auth.models import AdminAuditEvent, AuthSession, Base, User
from app.auth.security import COOKIE_NAME, create_session_token

admin_app.include_router(router)


class AdminFraudFlagTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(test_engine)

    def setUp(self) -> None:
        with Session(test_engine) as session:
            session.query(FraudFlag).delete()
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

    def create_flag(self, user_id: str, *, status: str = "OUVERTE") -> str:
        flag_id = str(uuid4())
        with Session(test_engine) as session:
            session.add(
                FraudFlag(
                    id=flag_id,
                    user_id=user_id,
                    type="unverified-type",
                    details="unverified private signal details",
                    statut=status,
                    examinee_at=datetime.now(UTC) if status != "OUVERTE" else None,
                )
            )
            session.commit()
        return flag_id

    def test_every_fraud_route_denies_anonymous_and_viewer_without_side_effects(self) -> None:
        viewer = self.create_user("VIEWER")
        flag_id = self.create_flag(viewer.id)
        viewer_headers = self.auth_headers(viewer)
        protected = [
            ("GET", "/admin/fraud/flags", None),
            ("GET", f"/admin/fraud/flags/{flag_id}", None),
            ("PATCH", f"/admin/fraud/flags/{flag_id}", {"statut": "EXAMINEE"}),
        ]
        for method, path, payload in protected:
            headers = {"origin": ORIGIN} if method == "PATCH" else {}
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

    def test_list_filters_and_bounds_without_unverified_details_or_user_pii(self) -> None:
        admin = self.create_user("ADMIN")
        viewer = self.create_user("VIEWER")
        first = self.create_flag(viewer.id)
        second = self.create_flag(viewer.id, status="EXAMINEE")
        headers = self.auth_headers(admin)

        status, body = request("GET", "/admin/fraud/flags?statut=OUVERTE&limit=1", headers=headers)
        self.assertEqual(status, 200, body.decode())
        response = json.loads(body)
        self.assertEqual((response["total"], response["page"], response["limit"]), (1, 1, 1))
        self.assertEqual(len(response["items"]), 1)
        item = response["items"][0]
        self.assertEqual(item["id"], first)
        self.assertEqual(item["user"], {"id": viewer.id, "pseudo": "VIEWER"})
        self.assertNotIn("type", item)
        self.assertNotIn("details", item)
        self.assertNotIn("watchSessionId", item)
        self.assertNotIn("email", body.decode())
        self.assertNotIn("unverified", body.decode())
        self.assertEqual(
            response["availability"],
            {
                "sourceDetails": "not_implemented",
                "watchSession": "not_implemented",
            },
        )

        status, _ = request("GET", "/admin/fraud/flags?statut=UNKNOWN", headers=headers)
        self.assertIn(status, {400, 422})
        status, _ = request("GET", "/admin/fraud/flags?limit=101", headers=headers)
        self.assertIn(status, {400, 422})
        status, _ = request("GET", f"/admin/fraud/flags/{second}", headers=headers)
        self.assertEqual(status, 200)
        status, detail_body = request("GET", f"/admin/fraud/flags/{first}", headers=headers)
        self.assertEqual(status, 200)
        detail = json.loads(detail_body)
        self.assertEqual(detail["user"], {"id": viewer.id, "pseudo": "VIEWER"})
        self.assertNotIn("type", detail)
        self.assertNotIn("details", detail)
        self.assertNotIn("email", detail_body.decode())
        self.assertEqual(detail["audit"], [])

    def test_status_update_audits_atomically_without_changing_account(self) -> None:
        admin = self.create_user("ADMIN")
        target = self.create_user("VIEWER")
        flag_id = self.create_flag(target.id)
        headers = self.auth_headers(admin)
        status, body = request(
            "PATCH",
            f"/admin/fraud/flags/{flag_id}",
            payload={"statut": "EXAMINEE", "note": "  Vérifié  "},
            headers=headers,
        )
        self.assertEqual(status, 200, body.decode())
        view = json.loads(body)
        self.assertEqual(view["statut"], "EXAMINEE")
        self.assertIsNotNone(view["examineeAt"])
        with Session(test_engine) as session:
            flag = session.get(FraudFlag, flag_id)
            user = session.get(User, target.id)
            audit = session.query(AdminAuditEvent).filter_by(entity_type="FraudFlag").one()
            self.assertEqual(flag.statut, "EXAMINEE")
            self.assertEqual(user.role, "VIEWER")
            self.assertTrue(user.active)
            self.assertEqual(audit.actor_id, admin.id)
            self.assertEqual(
                audit.metadata_json,
                {"previousStatut": "OUVERTE", "statut": "EXAMINEE", "note": "Vérifié"},
            )

        status, body = request(
            "PATCH", f"/admin/fraud/flags/{flag_id}", payload={"statut": "OUVERTE"}, headers=headers
        )
        self.assertEqual(status, 200, body.decode())
        self.assertIsNone(json.loads(body)["examineeAt"])

    def test_update_rejects_extra_fields_and_origin_and_audit_failure_rolls_back(self) -> None:
        admin = self.create_user("ADMIN")
        target = self.create_user("VIEWER")
        flag_id = self.create_flag(target.id)
        headers = self.auth_headers(admin)
        status, _ = request(
            "PATCH",
            f"/admin/fraud/flags/{flag_id}",
            payload={"statut": "EXAMINEE", "userId": admin.id},
            headers=headers,
        )
        self.assertIn(status, {400, 422})
        status, _ = request(
            "PATCH",
            f"/admin/fraud/flags/{flag_id}",
            payload={"statut": "EXAMINEE"},
            headers={"cookie": headers["cookie"], "origin": "https://attacker.example"},
        )
        self.assertEqual(status, 403)

        def fail_audit(_mapper, _connection, _target) -> None:
            raise RuntimeError("simulated audit failure")

        event.listen(AdminAuditEvent, "before_insert", fail_audit)
        try:
            with self.assertRaisesRegex(RuntimeError, "simulated audit failure"):
                request(
                    "PATCH",
                    f"/admin/fraud/flags/{flag_id}",
                    payload={"statut": "IGNOREE"},
                    headers=headers,
                )
        finally:
            event.remove(AdminAuditEvent, "before_insert", fail_audit)
        with Session(test_engine) as session:
            self.assertEqual(session.get(FraudFlag, flag_id).statut, "OUVERTE")
            self.assertEqual(
                session.query(AdminAuditEvent).filter_by(entity_type="FraudFlag").count(), 0
            )

    def test_admin_rate_limit_is_sixty_per_minute_per_actor_and_address(self) -> None:
        from starlette.requests import Request

        actor = f"test-{uuid4()}"
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/admin/fraud/flags",
            "headers": [],
            "query_string": b"",
            "client": ("192.0.2.10", 1234),
        }
        request_scope = Request(scope)
        with _lock:
            _attempts.pop(f"{actor}:192.0.2.10", None)
        try:
            for _ in range(60):
                enforce_admin_rate_limit(request_scope, actor)
            from fastapi import HTTPException

            with self.assertRaises(HTTPException) as error:
                enforce_admin_rate_limit(request_scope, actor)
            self.assertEqual(error.exception.status_code, 429)
        finally:
            with _lock:
                _attempts.pop(f"{actor}:192.0.2.10", None)

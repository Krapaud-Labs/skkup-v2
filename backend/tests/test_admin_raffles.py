"""Admin raffle configuration, lot management and draw deferral checks."""

from __future__ import annotations

import json
import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from admin_test_support import snapshot_database
from sqlalchemy import event
from sqlalchemy.orm import Session
from test_admin_users import ORIGIN, admin_app, request, test_engine

from app.admin.announcements import Announcement
from app.admin.models import Raffle, RaffleDrawAudit, RaffleLot, RaffleTicket, RaffleWinner, Sponsor
from app.admin.raffles import router
from app.auth.models import AdminAuditEvent, AuthSession, Base, User
from app.auth.security import COOKIE_NAME, create_session_token

admin_app.include_router(router)


class AdminRaffleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(test_engine)

    def setUp(self) -> None:
        with Session(test_engine) as session:
            session.query(RaffleWinner).delete()
            session.query(RaffleDrawAudit).delete()
            session.query(RaffleTicket).delete()
            session.query(RaffleLot).delete()
            session.query(Raffle).delete()
            session.query(Announcement).delete()
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

    def create_payload(self, sponsor_id: str | None = None) -> dict:
        opening = datetime.now(UTC) - timedelta(minutes=1)
        draw = datetime.now(UTC) + timedelta(days=2)
        lot = {
            "nom": "Lot test",
            "valeurEstimee": "125.50",
            "quantite": 1,
            "fournisseur": "Partenaire test",
            "imageUrl": "https://cdn.example.test/lot.png",
        }
        if sponsor_id:
            lot["sponsorId"] = sponsor_id
        return {
            "titre": "Tirage test",
            "description": "Description simple",
            "dateOuverture": opening.isoformat(),
            "dateTirage": draw.isoformat(),
            "engagementGraine": "a" * 64,
            "lots": [lot],
        }

    def test_all_admin_raffle_routes_deny_anonymous_and_viewer_without_effects(self) -> None:
        viewer = self.create_user("VIEWER")
        headers = self.auth_headers(viewer)
        paths = [
            ("GET", "/admin/raffles", None),
            ("GET", "/admin/raffles/missing", None),
            ("GET", "/admin/raffles/missing/history", None),
            ("POST", "/admin/raffles", self.create_payload()),
            ("PATCH", "/admin/raffles/missing", {"titre": "Interdit"}),
        ]
        for method, path, payload in paths:
            write_headers = {"origin": ORIGIN} if method in {"POST", "PATCH"} else {}
            with self.subTest(method=method, path=path, actor="anonymous"):
                before = snapshot_database(test_engine, Base.metadata)
                self.assertEqual(
                    request(method, path, payload=payload, headers=write_headers)[0], 401
                )
                self.assertEqual(snapshot_database(test_engine, Base.metadata), before)
            with self.subTest(method=method, path=path, actor="viewer"):
                before = snapshot_database(test_engine, Base.metadata)
                self.assertEqual(
                    request(
                        method,
                        path,
                        payload=payload,
                        headers={**write_headers, **headers},
                    )[0],
                    403,
                )
                self.assertEqual(snapshot_database(test_engine, Base.metadata), before)

    def test_admin_create_publishes_announcement_and_audits_atomically(self) -> None:
        admin = self.create_user("ADMIN")
        headers = self.auth_headers(admin)
        with Session(test_engine) as session:
            sponsor = Sponsor(
                id=str(uuid4()), nom="Sponsor test", logo_url="https://cdn.example.test/logo.png"
            )
            session.add(sponsor)
            session.commit()
            sponsor_id = sponsor.id
        payload = self.create_payload(sponsor_id)
        status, body = request("POST", "/admin/raffles", payload=payload, headers=headers)
        self.assertEqual(status, 200, body.decode())
        raffle = json.loads(body)
        self.assertEqual(raffle["statut"], "OUVERT")
        self.assertEqual(raffle["engagementGraine"], "a" * 64)
        self.assertNotIn("graineAleatoire", raffle)
        self.assertNotIn("resultatPublieAt", raffle)
        self.assertNotIn("empreinteParticipants", raffle)
        self.assertNotIn("entropiePublique", raffle)
        self.assertEqual(raffle["ticketsDistribues"], 0)
        self.assertEqual(raffle["gagnantsCount"], 0)
        self.assertEqual(raffle["lots"][0]["sponsor"]["id"], sponsor_id)
        self.assertNotIn("DRAW_SECRET", body.decode())

        with Session(test_engine) as session:
            saved = session.get(Raffle, raffle["id"])
            announcement = session.query(Announcement).one()
            audit = session.query(AdminAuditEvent).all()
            self.assertEqual(saved.statut, "OUVERT")
            self.assertEqual(announcement.status, "PUBLISHED")
            self.assertTrue(announcement.actif)
            self.assertEqual(announcement.created_by_id, admin.id)
            self.assertEqual(
                {event.action for event in audit},
                {"RAFFLE_CREATED", "ANNOUNCEMENT_CREATED", "ANNOUNCEMENT_PUBLISHED"},
            )
            self.assertEqual({event.actor_id for event in audit}, {admin.id})

        status, body = request("GET", "/admin/raffles?page=1&limit=1", headers=headers)
        self.assertEqual(status, 200, body.decode())
        feed = json.loads(body)
        self.assertEqual((feed["total"], feed["limit"]), (1, 1))
        self.assertEqual(feed["items"][0]["id"], raffle["id"])
        self.assertEqual(
            feed["availability"],
            {"draws": "scheduled", "tickets": "available"},
        )
        self.assertEqual(feed["items"][0]["drawAvailability"], "scheduled")
        self.assertEqual(feed["items"][0]["ticketsAvailability"], "available")
        self.assertEqual(feed["items"][0]["ticketsDistribues"], 0)
        self.assertEqual(feed["items"][0]["gagnantsCount"], 0)

        with Session(test_engine) as session:
            saved = session.get(Raffle, raffle["id"])
            saved.date_tirage = datetime.now(UTC) - timedelta(seconds=1)
            session.commit()
        feed = json.loads(request("GET", "/admin/raffles?page=1&limit=1", headers=headers)[1])
        self.assertEqual(feed["availability"], {"draws": "available", "tickets": "closed"})
        self.assertEqual(feed["items"][0]["drawAvailability"], "available")
        self.assertEqual(feed["items"][0]["ticketsAvailability"], "closed")

        with Session(test_engine) as session:
            saved = session.get(Raffle, raffle["id"])
            saved.statut = "TIRE"
            saved.graine_aleatoire = "b" * 64
            saved.empreinte_participants = "c" * 64
            saved.nombre_participants = 0
            saved.resultat_publie_at = datetime.now(UTC)
            session.commit()
        feed = json.loads(request("GET", "/admin/raffles?page=1&limit=1", headers=headers)[1])
        self.assertEqual(feed["availability"]["draws"], "drawn")
        self.assertEqual(feed["items"][0]["drawAvailability"], "drawn")
        history = json.loads(
            request("GET", f"/admin/raffles/{raffle['id']}/history", headers=headers)[1]
        )
        self.assertEqual(history["availability"]["draws"], "drawn")
        self.assertEqual(history["draws"], [])
        self.assertEqual(request("GET", "/admin/raffles?page=1&limit=101", headers=headers)[0], 422)

    def test_admin_updates_only_open_raffles_and_replaces_lots_with_audit(self) -> None:
        admin = self.create_user("ADMIN")
        headers = self.auth_headers(admin)
        status, body = request(
            "POST", "/admin/raffles", payload=self.create_payload(), headers=headers
        )
        self.assertEqual(status, 200, body.decode())
        raffle_id = json.loads(body)["id"]

        status, body = request(
            "PATCH",
            f"/admin/raffles/{raffle_id}",
            payload={
                "titre": "Updated",
                "lots": [
                    {
                        "nom": "Lot replacement",
                        "valeurEstimee": "2",
                        "quantite": 2,
                        "fournisseur": "Fournisseur",
                    }
                ],
            },
            headers=headers,
        )
        self.assertEqual(status, 200, body.decode())
        updated = json.loads(body)
        self.assertEqual(updated["titre"], "Updated")
        self.assertEqual(len(updated["lots"]), 1)
        self.assertEqual(updated["lots"][0]["nom"], "Lot replacement")
        with Session(test_engine) as session:
            self.assertEqual(session.query(RaffleLot).filter_by(raffle_id=raffle_id).count(), 1)
            self.assertEqual(
                session.query(AdminAuditEvent).filter_by(action="RAFFLE_UPDATED").count(), 1
            )
            updated_event = session.query(AdminAuditEvent).filter_by(action="RAFFLE_UPDATED").one()
            self.assertEqual(updated_event.metadata_json["previous"]["titre"], "Tirage test")
            self.assertEqual(updated_event.metadata_json["current"]["titre"], "Updated")

        with Session(test_engine) as session:
            session.get(Raffle, raffle_id).statut = "CLOTURE"
            session.commit()
        status, _ = request(
            "PATCH", f"/admin/raffles/{raffle_id}", payload={"titre": "No"}, headers=headers
        )
        self.assertEqual(status, 409)

    def test_invalid_raffle_configuration_and_draw_route_remain_unavailable(self) -> None:
        admin_headers = self.auth_headers(self.create_user("ADMIN"))
        payload = self.create_payload()
        payload["dateTirage"] = payload["dateOuverture"]
        status, _ = request("POST", "/admin/raffles", payload=payload, headers=admin_headers)
        self.assertIn(status, {400, 422})
        payload = self.create_payload()
        payload["lots"][0]["imageUrl"] = "javascript:alert(1)"
        status, _ = request("POST", "/admin/raffles", payload=payload, headers=admin_headers)
        self.assertIn(status, {400, 422})
        payload = self.create_payload()
        payload["unexpected"] = "mass assignment"
        status, _ = request("POST", "/admin/raffles", payload=payload, headers=admin_headers)
        self.assertIn(status, {400, 422})
        status, _ = request(
            "POST", "/admin/raffles/not-created/draw", payload={}, headers=admin_headers
        )
        self.assertEqual(status, 404)

    def test_mutations_require_allowed_origin_without_side_effects(self) -> None:
        admin = self.create_user("ADMIN")
        valid_headers = self.auth_headers(admin)
        status, body = request(
            "POST", "/admin/raffles", payload=self.create_payload(), headers=valid_headers
        )
        self.assertEqual(status, 200, body.decode())
        raffle_id = json.loads(body)["id"]
        for headers in ({}, {**valid_headers, "origin": "https://attacker.example"}):
            mutation_headers = {
                key: value for key, value in valid_headers.items() if key != "origin"
            } | headers
            for method, path, payload in (
                ("POST", "/admin/raffles", self.create_payload()),
                ("PATCH", f"/admin/raffles/{raffle_id}", {"titre": "Forbidden"}),
            ):
                with self.subTest(method=method, origin=headers.get("origin")):
                    before = snapshot_database(test_engine, Base.metadata)
                    self.assertEqual(
                        request(method, path, payload=payload, headers=mutation_headers)[0],
                        403,
                    )
                    self.assertEqual(snapshot_database(test_engine, Base.metadata), before)

    def test_patch_rejects_explicit_null_fields(self) -> None:
        admin_headers = self.auth_headers(self.create_user("ADMIN"))
        status, body = request(
            "POST", "/admin/raffles", payload=self.create_payload(), headers=admin_headers
        )
        self.assertEqual(status, 200, body.decode())
        raffle_id = json.loads(body)["id"]
        for patch in ({"titre": None}, {"description": None}, {"dateTirage": None}, {"lots": None}):
            with self.subTest(patch=patch):
                self.assertIn(
                    request(
                        "PATCH", f"/admin/raffles/{raffle_id}", payload=patch, headers=admin_headers
                    )[0],
                    {400, 422},
                )

    def test_audit_failure_rolls_back_raffle_lots_and_announcement(self) -> None:
        admin = self.create_user("ADMIN")
        headers = self.auth_headers(admin)

        def fail_raffle_audit(_mapper, _connection, target) -> None:
            if target.action == "RAFFLE_CREATED":
                raise RuntimeError("simulated audit failure")

        event.listen(AdminAuditEvent, "before_insert", fail_raffle_audit)
        try:
            with self.assertRaisesRegex(RuntimeError, "simulated audit failure"):
                request("POST", "/admin/raffles", payload=self.create_payload(), headers=headers)
        finally:
            event.remove(AdminAuditEvent, "before_insert", fail_raffle_audit)
        with Session(test_engine) as session:
            self.assertEqual(session.query(Raffle).count(), 0)
            self.assertEqual(session.query(RaffleLot).count(), 0)
            self.assertEqual(session.query(Announcement).count(), 0)
            self.assertEqual(session.query(AdminAuditEvent).count(), 0)

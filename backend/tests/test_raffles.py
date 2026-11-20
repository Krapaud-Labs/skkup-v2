"""Issue #9 draw API contracts and V1 auditability behavior."""

from __future__ import annotations

import hashlib
import os
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

os.environ.setdefault("DB_HOST", "127.0.0.1")
os.environ.setdefault("POSTGRES_DB", "raffles_contract_test")
os.environ.setdefault("POSTGRES_USER", "raffles_contract_test")
os.environ.setdefault("POSTGRES_PASSWORD", "raffles_contract_test")
os.environ.setdefault("AUTH_TOKEN_SECRET", "test-only-secret-with-at-least-32-bytes")
os.environ.setdefault("AUTH_ALLOWED_ORIGINS", "http://localhost:3010")

from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.admin.models import (
    Raffle,
    RaffleDrawAudit,
    RaffleLot,
    RaffleTicket,
    RaffleWinner,
)
from app.auth.models import AdminAuditEvent, Base, User
from app.raffles import (
    DrawInput,
    _bounded_random,
    execute_draw,
    raffle_participants,
    raffle_result,
)

ENGINE = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
SEED = "owner-secret-seed-v1"
ENTROPY = "public-entropy-supplied-by-admin"


def user(role: str, pseudo: str) -> User:
    return User(
        id=str(uuid4()),
        email=f"{uuid4().hex}@example.test",
        password_hash="test-only",
        pseudo=pseudo,
        role=role,
        active=True,
        session_version=0,
        points_balance=0,
        current_streak=0,
        max_streak=0,
        terms_accepted_at=datetime.now(UTC),
    )


class RaffleDrawContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(ENGINE)

    @classmethod
    def tearDownClass(cls) -> None:
        ENGINE.dispose()

    def setUp(self) -> None:
        with Session(ENGINE) as db:
            db.query(RaffleWinner).delete()
            db.query(RaffleDrawAudit).delete()
            db.query(RaffleTicket).delete()
            db.query(RaffleLot).delete()
            db.query(Raffle).delete()
            db.query(AdminAuditEvent).delete()
            db.query(User).delete()
            self.admin = user("ADMIN", "Admin test")
            self.viewer = user("VIEWER", "Viewer test")
            raffle = Raffle(
                id="raffle-draw-test",
                titre="Tirage de test",
                description="Test V1 draw behavior",
                date_ouverture=datetime.now(UTC) - timedelta(days=1),
                date_tirage=datetime.now(UTC) - timedelta(seconds=1),
                statut="OUVERT",
                engagement_graine=hashlib.sha256(SEED.encode()).hexdigest(),
            )
            raffle.lots = [
                RaffleLot(
                    id="lot-a",
                    raffle_id=raffle.id,
                    nom="Lot A",
                    valeur_estimee=10,
                    quantite=1,
                    fournisseur="Test",
                )
            ]
            raffle.tickets = [
                RaffleTicket(
                    id="ticket-b",
                    raffle_id=raffle.id,
                    user_id=self.viewer.id,
                    created_at=datetime.now(UTC),
                ),
                RaffleTicket(
                    id="ticket-a",
                    raffle_id=raffle.id,
                    user_id=self.admin.id,
                    created_at=datetime.now(UTC),
                ),
            ]
            db.add_all([self.admin, self.viewer, raffle])
            db.commit()
            self.admin_id, self.viewer_id = self.admin.id, self.viewer.id

    def test_draw_commitment_derivation_and_atomic_winner_publication(self) -> None:
        derived_seed = hashlib.sha256(f"{SEED}:{ENTROPY}".encode()).hexdigest()
        self.assertEqual(_bounded_random(derived_seed)(7), _bounded_random(derived_seed)(7))
        request = object()
        with Session(ENGINE, expire_on_commit=False) as db:
            admin = db.get(User, self.admin_id)
            with (
                patch("app.raffles._require_origin"),
                patch("app.raffles.require_admin", return_value=admin),
                patch("app.raffles.enforce_admin_rate_limit"),
            ):
                response = execute_draw(
                    "raffle-draw-test",
                    DrawInput(graineExploitant=SEED, entropiePublique=ENTROPY),
                    request,
                    db,
                )
                for mismatched_input in (
                    DrawInput(graineExploitant="other-operator-seed", entropiePublique=ENTROPY),
                    DrawInput(graineExploitant=SEED, entropiePublique="different-public-entropy"),
                ):
                    with self.assertRaises(HTTPException) as error:
                        execute_draw(
                            "raffle-draw-test", mismatched_input, request, db
                        )
                    self.assertEqual(error.exception.status_code, 409)
                    self.assertEqual(db.get(Raffle, "raffle-draw-test").statut, "TIRE")
                    self.assertEqual(
                        db.scalar(select(func.count()).select_from(RaffleWinner)), 1
                    )
                    self.assertEqual(
                        db.scalar(select(func.count()).select_from(RaffleDrawAudit)), 1
                    )
            self.assertEqual(response["graineAleatoire"], derived_seed)
            self.assertEqual(len(response["gagnants"]), 1)
            self.assertNotIn("userId", str(response))
            self.assertNotIn(SEED, str(response))
            self.assertEqual(
                db.scalar(select(Raffle).where(Raffle.id == "raffle-draw-test")).statut, "TIRE"
            )
            self.assertEqual(
                db.scalar(select(RaffleWinner.raffle_ticket_id)),
                response["gagnants"][0]["ticketId"],
            )
            audit = db.get(RaffleDrawAudit, "raffle-draw-test")
            self.assertEqual(audit.seed_commitment, hashlib.sha256(SEED.encode()).hexdigest())
            self.assertEqual(audit.algorithm, "sha256-counter-53bit-rejection-v1")
            with (
                patch("app.raffles._require_origin"),
                patch("app.raffles.require_admin", return_value=admin),
                patch("app.raffles.enforce_admin_rate_limit"),
            ):
                replay = execute_draw(
                    "raffle-draw-test",
                    DrawInput(graineExploitant=SEED, entropiePublique=ENTROPY),
                    request,
                    db,
                )
            self.assertEqual(replay, response)
            self.assertEqual(db.scalar(select(func.count()).select_from(RaffleWinner)), 1)
            self.assertEqual(len(list(db.scalars(select(RaffleDrawAudit)))), 1)

        with Session(ENGINE) as db:
            public = raffle_result("raffle-draw-test", db)
            self.assertEqual(public["graineAleatoire"], derived_seed)
            self.assertNotIn("userId", str(public))
            self.assertNotIn("email", str(public))
            self.assertNotIn(ENTROPY, str(public))
            first = raffle_participants("raffle-draw-test", db, page=0, taille=1)
            second = raffle_participants("raffle-draw-test", db, page=1, taille=1)
            self.assertEqual(first["participants"], ["ticket-a"])
            self.assertEqual(second["participants"], ["ticket-b"])
            self.assertEqual(first["empreinteParticipants"], public["empreinteParticipants"])

    def test_invalid_commitment_rolls_back_without_publishing(self) -> None:
        request = object()
        with Session(ENGINE, expire_on_commit=False) as db:
            admin = db.get(User, self.admin_id)
            with (
                patch("app.raffles._require_origin"),
                patch("app.raffles.require_admin", return_value=admin),
                patch("app.raffles.enforce_admin_rate_limit"),
            ):
                with self.assertRaises(HTTPException) as error:
                    execute_draw(
                        "raffle-draw-test",
                        DrawInput(graineExploitant="wrong-seed", entropiePublique=ENTROPY),
                        request,
                        db,
                    )
            self.assertEqual(error.exception.status_code, 409)
            self.assertEqual(db.get(Raffle, "raffle-draw-test").statut, "OUVERT")
            self.assertEqual(db.scalar(select(RaffleWinner.id)), None)
            self.assertIsNone(db.get(RaffleDrawAudit, "raffle-draw-test"))

    def test_non_admin_and_bad_origin_are_rejected_before_any_draw_mutation(self) -> None:
        request = object()
        with Session(ENGINE, expire_on_commit=False) as db:
            db.get(User, self.viewer_id)
            with patch("app.raffles._require_origin", side_effect=HTTPException(403)):
                with self.assertRaises(HTTPException) as error:
                    execute_draw(
                        "raffle-draw-test",
                        DrawInput(graineExploitant=SEED, entropiePublique=ENTROPY),
                        request,
                        db,
                    )
            self.assertEqual(error.exception.status_code, 403)
            with (
                patch("app.raffles._require_origin"),
                patch("app.raffles.require_admin", side_effect=HTTPException(403)),
            ):
                with self.assertRaises(HTTPException) as error:
                    execute_draw(
                        "raffle-draw-test",
                        DrawInput(graineExploitant=SEED, entropiePublique=ENTROPY),
                        request,
                        db,
                    )
            self.assertEqual(error.exception.status_code, 403)
            self.assertEqual(db.get(Raffle, "raffle-draw-test").statut, "OUVERT")
            self.assertEqual(db.scalar(select(RaffleWinner.id)), None)
            self.assertIsNone(db.get(RaffleDrawAudit, "raffle-draw-test"))


if __name__ == "__main__":
    unittest.main()

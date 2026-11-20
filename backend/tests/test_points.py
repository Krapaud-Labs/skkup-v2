"""Transactional service tests for Viewer points, streaks and rewards."""

from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.admin.models import Raffle, RaffleTicket
from app.auth.models import Base, User
from app.points.models import DailyCheckin, PointsTransaction, RewardTicket, ScratchCardGrant
from app.points.service import (
    _next_streak_milestone,
    apply_points_change,
    award_reward_ticket,
    checkin_daily,
    scratch_history,
    scratch_legacy_card,
    scratch_reward_outcome,
    scratch_reward_ticket,
)

ENGINE = create_engine("sqlite://")
Base.metadata.create_all(ENGINE)
PARIS = ZoneInfo("Europe/Paris")


def make_user(session: Session, user_id: str = "viewer-1") -> User:
    user = User(
        id=user_id,
        email=f"{user_id}@example.test",
        password_hash="unused",
        pseudo="Viewer",
        role="VIEWER",
        active=True,
        session_version=0,
        points_balance=0,
        current_streak=0,
        max_streak=0,
        terms_accepted_at=datetime(2029, 1, 1, tzinfo=UTC),
    )
    session.add(user)
    session.commit()
    return user


class ViewerPointsServiceTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        ENGINE.dispose()

    def setUp(self) -> None:
        with Session(ENGINE) as session:
            session.query(RaffleTicket).delete()
            session.query(Raffle).delete()
            session.query(RewardTicket).delete()
            session.query(ScratchCardGrant).delete()
            session.query(PointsTransaction).delete()
            session.query(DailyCheckin).delete()
            session.query(User).delete()
            session.commit()
            make_user(session)

    def test_daily_ticket_replaces_direct_five_points_and_replay_is_stable(self) -> None:
        first_day = datetime(2030, 1, 1, 9, tzinfo=PARIS)
        with Session(ENGINE, expire_on_commit=False) as session:
            first = checkin_daily(session, "viewer-1", now=first_day)
            replay = checkin_daily(session, "viewer-1", now=first_day + timedelta(hours=2))
            user = session.get(User, "viewer-1")
            ledger_count = session.scalar(select(func.count()).select_from(PointsTransaction))

        self.assertEqual(first["streakActuel"], 1)
        self.assertEqual([row["categorie"] for row in first["ticketsAttribues"]], ["CLASSIC"])
        self.assertEqual(replay, first)
        self.assertEqual(user.points_balance, 0)
        self.assertEqual(ledger_count, 0)

    def test_d14_d15_streak_rewards_and_v1_cards_are_preserved(self) -> None:
        day_one = datetime(2030, 2, 1, 9, tzinfo=PARIS)
        by_day: dict[int, dict] = {}
        with Session(ENGINE, expire_on_commit=False) as session:
            for day in range(1, 31):
                by_day[day] = checkin_daily(
                    session,
                    "viewer-1",
                    now=day_one + timedelta(days=day - 1),
                )

        expected = {
            3: ["CLASSIC", "CLASSIC"],
            7: ["CLASSIC", "CLASSIC", "CLASSIC"],
            14: ["CLASSIC", "CLASSIC", "CLASSIC", "PREMIUM"],
            30: ["CLASSIC", "CLASSIC", "CLASSIC", "PREMIUM", "PREMIUM"],
        }
        for day, categories in expected.items():
            self.assertEqual(
                sorted(row["categorie"] for row in by_day[day]["ticketsAttribues"]),
                sorted(categories),
            )
            self.assertTrue(by_day[day]["carteAGratterDebloquee"])
            self.assertIsNotNone(by_day[day]["carteDebloquee"])
        self.assertFalse(by_day[2]["carteAGratterDebloquee"])
        with Session(ENGINE, expire_on_commit=False) as session:
            replay = checkin_daily(
                session,
                "viewer-1",
                now=day_one + timedelta(days=13, hours=1),
            )
        self.assertEqual(replay, by_day[14])

    def test_days_after_thirty_keep_only_v1_card_schedule(self) -> None:
        start = datetime(2030, 3, 1, 9, tzinfo=PARIS)
        with Session(ENGINE, expire_on_commit=False) as session:
            for day in range(1, 41):
                result = checkin_daily(session, "viewer-1", now=start + timedelta(days=day - 1))
        self.assertTrue(result["carteAGratterDebloquee"])
        self.assertEqual(result["palierCarte"], 40)
        self.assertEqual(result["carteDebloquee"]["streakPalier"], 40)
        self.assertEqual(result["carteDebloquee"]["gainType"], "TICKET")
        self.assertEqual(result["carteDebloquee"]["gainMontant"], 1)
        self.assertEqual(
            [ticket["categorie"] for ticket in result["ticketsAttribues"]], ["CLASSIC"]
        )

    def test_next_v1_scratch_card_milestone_after_day_thirty(self) -> None:
        self.assertEqual(_next_streak_milestone(30), 40)
        self.assertEqual(_next_streak_milestone(31), 40)
        self.assertEqual(_next_streak_milestone(39), 40)
        self.assertEqual(_next_streak_milestone(40), 50)

    def test_points_ledger_and_balance_change_atomically_and_idempotently(self) -> None:
        with Session(ENGINE, expire_on_commit=False) as session:
            credit = apply_points_change(
                session,
                user_id="viewer-1",
                amount=25,
                type="WATCH_TIME",
                idempotency_key="watch:test-session",
            )
            session.commit()
            replay = apply_points_change(
                session,
                user_id="viewer-1",
                amount=25,
                type="WATCH_TIME",
                idempotency_key="watch:test-session",
            )
            self.assertEqual(credit.id, replay.id)
            with self.assertRaises(HTTPException) as error:
                apply_points_change(
                    session,
                    user_id="viewer-1",
                    amount=-26,
                    type="SHOP_PURCHASE",
                    idempotency_key="purchase:insufficient",
                )
            self.assertEqual(error.exception.status_code, 409)
            session.rollback()

        with Session(ENGINE) as session:
            user = session.get(User, "viewer-1")
            ledger_sum = session.scalar(select(func.sum(PointsTransaction.amount)))
            self.assertEqual(user.points_balance, 25)
            self.assertEqual(ledger_sum, user.points_balance)
            self.assertEqual(user.points_balance, 25)

    def test_scratch_awarded_ticket_is_always_classic_and_replay_safe(self) -> None:
        with Session(ENGINE, expire_on_commit=False) as session:
            first = award_reward_ticket(
                session,
                user_id="viewer-1",
                category="PREMIUM",
                source="SCRATCH_CARD",
                source_id="scratch-1",
                idempotency_key="scratch:scratch-1",
            )
            replay = award_reward_ticket(
                session,
                user_id="viewer-1",
                category="PREMIUM",
                source="SCRATCH_CARD",
                source_id="scratch-1",
                idempotency_key="scratch:scratch-1",
            )
            session.commit()
        self.assertEqual(first.category, "CLASSIC")
        self.assertEqual(first.id, replay.id)

    def test_classic_scratch_distribution_uses_exact_integer_boundaries(self) -> None:
        cases = {
            0: ("NO_WIN", 0, 0),
            29: ("NO_WIN", 0, 0),
            30: ("POINTS", 5, 0),
            44: ("POINTS", 5, 0),
            45: ("POINTS", 10, 0),
            54: ("POINTS", 10, 0),
            55: ("POINTS", 15, 0),
            59: ("POINTS", 15, 0),
            60: ("SCRATCH_TICKET", 0, 1),
            99: ("SCRATCH_TICKET", 0, 1),
        }
        for roll, expected in cases.items():
            with self.subTest(roll=roll):
                self.assertEqual(
                    scratch_reward_outcome("CLASSIC", lambda _, roll=roll: roll), expected
                )

    def test_premium_scratch_known_outcomes_and_contest_access_probability(self) -> None:
        cases = {
            0: ("POINTS", 30, 0),
            89: ("POINTS", 30, 0),
            90: ("POINTS", 40, 0),
            94: ("POINTS", 40, 0),
            95: ("POINTS", 50, 0),
            98: ("POINTS", 50, 0),
            99: ("RAFFLE_TICKET", 0, 0),
        }
        for roll, expected in cases.items():
            with self.subTest(roll=roll):
                self.assertEqual(
                    scratch_reward_outcome("PREMIUM", lambda _, roll=roll: roll), expected
                )

    def test_legacy_ticket_reward_creates_scratch_classic_not_raffle_entry(self) -> None:
        with Session(ENGINE, expire_on_commit=False) as session:
            checkin = DailyCheckin(
                id="checkin-legacy",
                user_id="viewer-1",
                local_day=datetime(2030, 1, 1).date(),
                streak_after=3,
                max_streak_after=3,
                points_balance_after=0,
                scratch_card_due=True,
            )
            card = ScratchCardGrant(
                id="scratch-legacy",
                user_id="viewer-1",
                daily_checkin_id=checkin.id,
                streak_milestone=3,
                legacy_ticket_preset=False,
            )
            raffle = Raffle(
                id="raffle-open",
                titre="Ouvert",
                description="Test",
                date_ouverture=datetime(2020, 1, 1, tzinfo=UTC),
                date_tirage=datetime(2099, 1, 1, tzinfo=UTC),
                statut="OUVERT",
                engagement_graine="a" * 64,
            )
            session.add_all([checkin, card, raffle])
            session.commit()
            result = scratch_legacy_card(session, "viewer-1", card.id, randbelow=lambda _: 99)
            scratch_tickets = list(session.scalars(select(RewardTicket)))
            raffle_tickets = list(session.scalars(select(RaffleTicket)))
        self.assertEqual(result["outcome"]["type"], "SCRATCH_TICKET")
        self.assertEqual(len(scratch_tickets), 1)
        self.assertEqual(scratch_tickets[0].category, "CLASSIC")
        self.assertEqual(scratch_tickets[0].source, "SCRATCH_CARD")
        self.assertEqual(raffle_tickets, [])

    def test_premium_scratch_without_open_raffle_is_blocked_before_rng(self) -> None:
        with Session(ENGINE, expire_on_commit=False) as session:
            ticket = RewardTicket(
                id="premium-pending",
                user_id="viewer-1",
                category="PREMIUM",
                source="DAILY_LOGIN",
                source_id="source-1",
                idempotency_key="premium-pending",
            )
            session.add(ticket)
            session.commit()
            with self.assertRaises(HTTPException) as error:
                scratch_reward_ticket(
                    session,
                    "viewer-1",
                    ticket.id,
                    randbelow=lambda _: self.fail(
                        "RNG must not run without an eligible open raffle"
                    ),
                )
            self.assertEqual(error.exception.status_code, 409)
            session.refresh(ticket)
            self.assertIsNone(ticket.scratched_at)
            self.assertIsNone(ticket.consumed_at)
            self.assertEqual(session.scalar(select(func.count()).select_from(PointsTransaction)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(RaffleTicket)), 0)

    def test_premium_one_percent_awards_raffle_ticket_atomically(self) -> None:
        with Session(ENGINE, expire_on_commit=False) as session:
            raffle = Raffle(
                id="premium-open-raffle",
                titre="Concours ouvert",
                description="Accès obtenu par grattage PREMIUM",
                date_ouverture=datetime(2020, 1, 1, tzinfo=UTC),
                date_tirage=datetime.now(UTC) + timedelta(days=2),
                statut="OUVERT",
                engagement_graine="a" * 64,
            )
            ticket = RewardTicket(
                id="premium-1-percent",
                user_id="viewer-1",
                category="PREMIUM",
                source="DAILY_LOGIN",
                source_id="source-premium-1-percent",
                idempotency_key="premium-1-percent",
            )
            session.add_all([raffle, ticket])
            session.commit()

            result = scratch_reward_ticket(
                session, "viewer-1", ticket.id, randbelow=lambda _: 99
            )
            history = scratch_history(session, "viewer-1", page=1, limit=20)
            raffle_entries = list(session.scalars(select(RaffleTicket)))
            reward_tickets = list(session.scalars(select(RewardTicket)))
            transactions = list(session.scalars(select(PointsTransaction)))
            session.refresh(ticket)

        self.assertEqual(result["outcome"]["type"], "RAFFLE_TICKET")
        self.assertTrue(result["outcome"]["raffleTicketAwarded"])
        self.assertEqual(result["outcome"]["raffleId"], "premium-open-raffle")
        self.assertEqual(result["outcome"]["raffleTicketId"], raffle_entries[0].id)
        self.assertEqual(len(raffle_entries), 1)
        self.assertEqual(len(reward_tickets), 1)
        self.assertEqual(raffle_entries[0].raffle_id, "premium-open-raffle")
        self.assertEqual(ticket.category, "PREMIUM")
        self.assertIsNotNone(ticket.consumed_at)
        self.assertEqual(transactions, [])
        history_item = next(item for item in history["items"] if item["id"] == ticket.id)
        self.assertEqual(history_item["outcome"], "RAFFLE_TICKET")
        self.assertEqual(history_item["scratchTicketsAwarded"], 0)
        self.assertTrue(history_item["raffleTicketAwarded"])

    def test_checkin_rolls_back_all_mutations_when_award_fails(self) -> None:
        now = datetime(2030, 4, 1, 9, tzinfo=PARIS)
        with Session(ENGINE, expire_on_commit=False) as session:
            with patch(
                "app.points.service.award_reward_ticket",
                side_effect=RuntimeError("failure"),
            ):
                with self.assertRaises(RuntimeError):
                    checkin_daily(session, "viewer-1", now=now)
            self.assertEqual(session.scalar(select(func.count()).select_from(DailyCheckin)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(ScratchCardGrant)), 0)
            self.assertEqual(session.scalar(select(func.count()).select_from(RewardTicket)), 0)
            user = session.get(User, "viewer-1")
            self.assertEqual(user.current_streak, 0)
            self.assertIsNone(user.last_visit_at)

    def test_database_unique_user_day_constraint_blocks_duplicate_event(self) -> None:
        now = datetime(2030, 5, 1, 9, tzinfo=PARIS)
        with Session(ENGINE) as session:
            checkin_daily(session, "viewer-1", now=now)
            session.add(
                DailyCheckin(
                    id=str(uuid4()),
                    user_id="viewer-1",
                    local_day=now.date(),
                    streak_after=1,
                    max_streak_after=1,
                    scratch_card_due=False,
                )
            )
            with self.assertRaises(IntegrityError):
                session.flush()
            session.rollback()


if __name__ == "__main__":
    unittest.main()

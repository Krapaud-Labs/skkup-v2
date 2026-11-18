"""Transactional points ledger and daily Viewer progression operations."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.models import User
from app.points.models import DailyCheckin, PointsTransaction, RewardTicket, ScratchCardGrant
from app.timezone import business_day

STREAK_SCRATCH_CARD_MILESTONES = frozenset({3, 7, 14, 30})
STREAK_EXTRA_TICKETS: dict[int, dict[str, int]] = {
    3: {"CLASSIC": 1},
    7: {"CLASSIC": 2},
    14: {"CLASSIC": 2, "PREMIUM": 1},
    30: {"CLASSIC": 2, "PREMIUM": 2},
}
KNOWN_STREAK_MILESTONES = (3, 7, 14, 30)
POINTS_TRANSACTION_TYPES = frozenset(
    {
        "VISITE_QUOTIDIENNE",
        "WATCH_TIME",
        "CARTE_A_GRATTER",
        "AJUSTEMENT_ADMIN",
        "SHOP_PURCHASE",
    }
)


def _normalise_datetime(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _datetime_text(value: datetime) -> str:
    return _normalise_datetime(value).astimezone(UTC).isoformat().replace("+00:00", "Z")


def _card_is_due(streak: int) -> bool:
    return streak in STREAK_SCRATCH_CARD_MILESTONES or (streak > 30 and streak % 10 == 0)


def _next_streak_milestone(streak: int) -> int | None:
    if streak >= 30:
        return (streak // 10 + 1) * 10
    return next(milestone for milestone in KNOWN_STREAK_MILESTONES if milestone > streak)


def _tickets_for_checkin(db: Session, checkin_id: str) -> list[RewardTicket]:
    return list(
        db.scalars(
            select(RewardTicket)
            .where(RewardTicket.source_id == checkin_id)
            .order_by(RewardTicket.idempotency_key)
        )
    )


def _checkin_result(
    checkin: DailyCheckin,
    tickets: list[RewardTicket],
    card: ScratchCardGrant | None,
) -> dict:
    return {
        "id": checkin.id,
        "jourConnexion": checkin.local_day.isoformat(),
        "streakActuel": checkin.streak_after,
        "streakMax": checkin.max_streak_after,
        "soldePoints": checkin.points_balance_after,
        "pointsCredites": 0,
        "ticketsAttribues": [
            {
                "id": ticket.id,
                "categorie": ticket.category,
                "origine": ticket.source,
            }
            for ticket in tickets
        ],
        "carteAGratterDebloquee": checkin.scratch_card_due,
        "palierCarte": checkin.streak_after if checkin.scratch_card_due else None,
        "carteDebloquee": (
            {
                "id": card.id,
                "userId": card.user_id,
                "streakPalier": card.streak_milestone,
                "grattee": False,
                "gainType": "TICKET" if card.legacy_ticket_preset else None,
                "gainMontant": 1 if card.legacy_ticket_preset else None,
                "gainPrepareAt": None,
                "createdAt": _datetime_text(card.created_at),
                "gratteeAt": None,
            }
            if card
            else None
        ),
    }


def _replayed_checkin_result(db: Session, checkin: DailyCheckin) -> dict:
    card = db.scalar(
        select(ScratchCardGrant).where(ScratchCardGrant.daily_checkin_id == checkin.id)
    )
    return _checkin_result(checkin, _tickets_for_checkin(db, checkin.id), card)


def award_reward_ticket(
    db: Session,
    *,
    user_id: str,
    category: str,
    source: str,
    source_id: str,
    idempotency_key: str,
) -> RewardTicket:
    """Create one unassigned reward ticket; raffle consumption belongs to #9.

    D-16 fixes every ticket awarded by a scratch card to CLASSIC. The scratch
    outcome itself is deliberately selected and persisted by the #9 flow.
    """
    if source not in {"DAILY_LOGIN", "STREAK_MILESTONE", "SCRATCH_CARD"}:
        raise ValueError("Unsupported reward ticket source.")
    if category not in {"CLASSIC", "PREMIUM"}:
        raise ValueError("Unsupported reward ticket category.")
    assigned_category = "CLASSIC" if source == "SCRATCH_CARD" else category
    existing = db.scalar(
        select(RewardTicket).where(
            RewardTicket.user_id == user_id,
            RewardTicket.idempotency_key == idempotency_key,
        )
    )
    if existing:
        if existing.category != assigned_category or existing.source != source:
            raise HTTPException(status_code=409, detail="Clé de récompense déjà utilisée.")
        return existing
    ticket = RewardTicket(
        id=str(uuid4()),
        user_id=user_id,
        category=assigned_category,
        source=source,
        source_id=source_id,
        idempotency_key=idempotency_key,
    )
    db.add(ticket)
    db.flush()
    return ticket


def apply_points_change(
    db: Session,
    *,
    user_id: str,
    amount: int,
    type: str,
    idempotency_key: str,
    now: datetime | None = None,
) -> PointsTransaction:
    """Atomically apply a signed points delta and append its ledger entry."""
    if amount == 0:
        raise HTTPException(status_code=400, detail="Le montant doit être différent de zéro.")
    if type not in POINTS_TRANSACTION_TYPES:
        raise HTTPException(status_code=400, detail="Type de transaction de points invalide.")
    if not idempotency_key or len(idempotency_key) > 160:
        raise HTTPException(status_code=400, detail="Clé d’idempotence invalide.")
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    previous = db.scalar(
        select(PointsTransaction).where(
            PointsTransaction.user_id == user_id,
            PointsTransaction.idempotency_key == idempotency_key,
        )
    )
    if previous is not None:
        if previous.amount != amount or previous.type != type:
            raise HTTPException(status_code=409, detail="Clé de points déjà utilisée.")
        return previous
    balance = user.points_balance + amount
    if balance < 0:
        raise HTTPException(status_code=409, detail="Solde de points insuffisant.")
    transaction = PointsTransaction(
        id=str(uuid4()),
        user_id=user_id,
        amount=amount,
        balance_after=balance,
        type=type,
        idempotency_key=idempotency_key,
        created_at=_normalise_datetime(now or datetime.now(UTC)).astimezone(UTC),
    )
    user.points_balance = balance
    db.add(transaction)
    db.flush()
    return transaction


def checkin_daily(db: Session, user_id: str, *, now: datetime | None = None) -> dict:
    try:
        return _checkin_daily(db, user_id, now=now)
    except Exception:
        db.rollback()
        raise


def _checkin_daily(db: Session, user_id: str, *, now: datetime | None = None) -> dict:
    moment = _normalise_datetime(now or datetime.now(UTC)).astimezone(UTC)
    today = business_day(moment)
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    existing = db.scalar(
        select(DailyCheckin).where(
            DailyCheckin.user_id == user_id,
            DailyCheckin.local_day == today,
        )
    )
    if existing is not None:
        result = _replayed_checkin_result(db, existing)
        db.rollback()
        return result

    last_visit_day = (
        business_day(_normalise_datetime(user.last_visit_at)) if user.last_visit_at else None
    )
    if last_visit_day == today:
        # Protect accounts whose last-visit marker predates the event ledger
        # from receiving a second reward after a partial/manual migration.
        db.rollback()
        raise HTTPException(status_code=409, detail="Visite déjà enregistrée aujourd’hui.")

    streak = user.current_streak + 1 if last_visit_day == today - timedelta(days=1) else 1
    max_streak = max(user.max_streak, streak)
    checkin = DailyCheckin(
        id=str(uuid4()),
        user_id=user_id,
        local_day=today,
        streak_after=streak,
        max_streak_after=max_streak,
        points_balance_after=user.points_balance,
        scratch_card_due=_card_is_due(streak),
        created_at=moment,
    )
    user.last_visit_at = moment
    user.current_streak = streak
    user.max_streak = max_streak
    db.add(checkin)
    db.flush()

    card = None
    if checkin.scratch_card_due:
        card = ScratchCardGrant(
            id=str(uuid4()),
            user_id=user_id,
            daily_checkin_id=checkin.id,
            streak_milestone=streak,
            legacy_ticket_preset=streak > 30 and streak % 10 == 0,
            created_at=moment,
        )
        db.add(card)

    tickets = [
        award_reward_ticket(
            db,
            user_id=user_id,
            category="CLASSIC",
            source="DAILY_LOGIN",
            source_id=checkin.id,
            idempotency_key=f"{checkin.id}:daily:classic",
        )
    ]
    for category, count in STREAK_EXTRA_TICKETS.get(streak, {}).items():
        for index in range(count):
            tickets.append(
                award_reward_ticket(
                    db,
                    user_id=user_id,
                    category=category,
                    source="STREAK_MILESTONE",
                    source_id=checkin.id,
                    idempotency_key=f"{checkin.id}:streak:{category.lower()}:{index}",
                )
            )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        committed = db.scalar(
            select(DailyCheckin).where(
                DailyCheckin.user_id == user_id,
                DailyCheckin.local_day == today,
            )
        )
        if committed is None:
            raise
        return _replayed_checkin_result(db, committed)
    return _checkin_result(checkin, tickets, card)


def get_points_summary(db: Session, user_id: str) -> dict:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    ledger_balance = db.scalar(
        select(func.coalesce(func.sum(PointsTransaction.amount), 0)).where(
            PointsTransaction.user_id == user_id
        )
    )
    if ledger_balance != user.points_balance:
        raise HTTPException(status_code=500, detail="Le solde et le journal de points divergent.")
    available = db.execute(
        select(RewardTicket.category, func.count(RewardTicket.id))
        .where(RewardTicket.user_id == user_id, RewardTicket.consumed_at.is_(None))
        .group_by(RewardTicket.category)
    ).all()
    return {
        "soldePoints": user.points_balance,
        "streakActuel": user.current_streak,
        "streakMax": user.max_streak,
        "derniereVisiteAt": user.last_visit_at,
        "prochainPalierStreak": _next_streak_milestone(user.current_streak),
        "ticketsDisponibles": {category: count for category, count in available},
    }


def points_history(db: Session, user_id: str, *, page: int, limit: int) -> dict:
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    where = PointsTransaction.user_id == user_id
    transactions = list(
        db.scalars(
            select(PointsTransaction)
            .where(where)
            .order_by(PointsTransaction.created_at.desc(), PointsTransaction.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    )
    total = db.scalar(select(func.count()).select_from(PointsTransaction).where(where)) or 0
    return {
        "transactions": [
            {
                "id": row.id,
                "userId": row.user_id,
                "type": row.type,
                "montant": row.amount,
                "watchSessionId": None,
                "shopPurchaseId": None,
                "createdAt": _datetime_text(row.created_at),
            }
            for row in transactions
        ],
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": (total + limit - 1) // limit,
    }


def reward_ticket_inventory(db: Session, user_id: str, *, page: int, limit: int) -> dict:
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    where = (RewardTicket.user_id == user_id) & RewardTicket.consumed_at.is_(None)
    tickets = list(
        db.scalars(
            select(RewardTicket)
            .where(where)
            .order_by(RewardTicket.created_at.desc(), RewardTicket.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    )
    total = db.scalar(select(func.count()).select_from(RewardTicket).where(where)) or 0
    return {
        "tickets": [
            {
                "id": ticket.id,
                "categorie": ticket.category,
                "origine": ticket.source,
                "obtenuLe": ticket.created_at,
            }
            for ticket in tickets
        ],
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": (total + limit - 1) // limit,
    }

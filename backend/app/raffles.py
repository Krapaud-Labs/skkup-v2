"""Viewer raffle participation and public, replayable draw results."""

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, StrictStr
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.admin.models import Raffle, RaffleDrawAudit, RaffleLot, RaffleTicket, RaffleWinner
from app.admin.rate_limit import enforce_admin_rate_limit
from app.auth.authorization import require_admin
from app.auth.models import AdminAuditEvent, User
from app.auth.routes import _require_origin
from app.auth.session import claims_for_request
from app.db import get_db
from app.points.models import PointsTransaction
from app.points.service import apply_points_change

public_router = APIRouter(tags=["raffles"])
viewer_router = APIRouter(prefix="/me", tags=["viewer-raffles"])
admin_draw_router = APIRouter(prefix="/admin/raffles", tags=["admin-raffles"])
DatabaseSession = Annotated[Session, Depends(get_db)]
ENTRY_COST = 2500
DRAW_ALGORITHM = "sha256-counter-53bit-rejection-v1"


class DrawInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    graineExploitant: StrictStr = Field(min_length=1, max_length=512)
    entropiePublique: StrictStr = Field(min_length=1, max_length=512)


def _current_user(request: Request, db: Session) -> User:
    _, user, _ = claims_for_request(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Session invalide.")
    return user


def _iso_utc(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _pages(total: int, page: int, limit: int) -> dict:
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "totalPages": (total + limit - 1) // limit,
    }


def _canonical_hash(ticket_ids: list[str]) -> str:
    ids = sorted(ticket_ids)
    encoded = f"{len(ids)}:" + "".join(f"{len(item)}:{item}" for item in ids)
    return hashlib.sha256(encoded.encode()).hexdigest()


def _bounded_random(seed: str):
    counter = 0
    max_53 = 2**53

    def draw(bound: int) -> int:
        nonlocal counter
        if bound <= 0:
            raise ValueError("bound must be positive")
        limit = max_53 - max_53 % bound
        while True:
            block = hashlib.sha256(f"{seed}:{counter}".encode()).digest()
            counter += 1
            value = int.from_bytes(block[:8], "big") >> 11
            if value < limit:
                return value % bound

    return draw


def _pick_winners(seed: str, tickets: list[RaffleTicket], lots: list[RaffleLot]):
    hat = sorted(ticket.id for ticket in tickets)
    rng = _bounded_random(seed)
    winners = []
    for lot in sorted(lots, key=lambda item: item.id):
        for _ in range(max(0, lot.quantite)):
            if not hat:
                return winners
            ticket_id = hat.pop(rng(len(hat)))
            winners.append((lot, ticket_id))
    return winners


def _stored_draw_result(db: Session, raffle: Raffle) -> dict:
    winners = list(
        db.execute(
            select(RaffleWinner, RaffleTicket)
            .join(RaffleTicket, RaffleWinner.raffle_ticket_id == RaffleTicket.id)
            .where(RaffleWinner.raffle_id == raffle.id)
            .order_by(RaffleWinner.rank)
        )
    )
    return {
        "raffleId": raffle.id,
        "graineAleatoire": raffle.graine_aleatoire,
        "empreinteParticipants": raffle.empreinte_participants,
        "resultatPublieAt": _iso_utc(raffle.resultat_publie_at),
        "nombreTickets": raffle.nombre_participants or 0,
        "gagnants": [{"lotId": winner.lot_id, "ticketId": ticket.id} for winner, ticket in winners],
    }


def _public_raffle(raffle: Raffle, ticket_count: int) -> dict:
    return {
        "id": raffle.id,
        "titre": raffle.titre,
        "description": raffle.description,
        "dateOuverture": raffle.date_ouverture.isoformat(),
        "dateTirage": raffle.date_tirage.isoformat(),
        "statut": raffle.statut,
        "resultatPublieAt": raffle.resultat_publie_at.isoformat()
        if raffle.resultat_publie_at
        else None,
        "ticketsDistribues": ticket_count,
        "lots": [
            {
                "id": lot.id,
                "nom": lot.nom,
                "valeurEstimee": str(lot.valeur_estimee),
                "quantite": lot.quantite,
                "fournisseur": lot.fournisseur,
                "imageUrl": lot.image_url,
            }
            for lot in raffle.lots
        ],
    }


@public_router.get("/raffles")
def list_raffles(db: DatabaseSession):
    raffles = list(
        db.scalars(
            select(Raffle).options(selectinload(Raffle.lots)).order_by(Raffle.date_tirage.desc())
        )
    )
    return [
        _public_raffle(
            raffle,
            db.scalar(
                select(func.count())
                .select_from(RaffleTicket)
                .where(RaffleTicket.raffle_id == raffle.id)
            )
            or 0,
        )
        for raffle in raffles
    ]


@public_router.get("/raffles/{raffle_id}")
def raffle_detail(raffle_id: str, db: DatabaseSession):
    raffle = db.scalar(
        select(Raffle).options(selectinload(Raffle.lots)).where(Raffle.id == raffle_id)
    )
    if raffle is None:
        raise HTTPException(status_code=404, detail="Tirage introuvable.")
    count = (
        db.scalar(
            select(func.count())
            .select_from(RaffleTicket)
            .where(RaffleTicket.raffle_id == raffle.id)
        )
        or 0
    )
    return _public_raffle(raffle, count)


@viewer_router.post("/raffles/{raffle_id}/register")
def register_raffle(raffle_id: str, request: Request, db: DatabaseSession):
    _require_origin(request)
    user = _current_user(request, db)
    try:
        user = db.scalar(select(User).where(User.id == user.id).with_for_update())
        if user is None:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        existing = db.scalar(
            select(RaffleTicket).where(
                RaffleTicket.user_id == user.id, RaffleTicket.raffle_id == raffle_id
            )
        )
        if existing:
            txn = db.scalar(
                select(PointsTransaction).where(
                    PointsTransaction.user_id == user.id,
                    PointsTransaction.idempotency_key == f"raffle-entry:{raffle_id}",
                )
            )
            if txn is None:
                raise HTTPException(
                    status_code=500, detail="Participation et registre de points divergents."
                )
            db.rollback()
            return {
                "id": existing.id,
                "raffleId": raffle_id,
                "coutPoints": ENTRY_COST,
                "soldePoints": txn.balance_after,
                "createdAt": existing.created_at.isoformat(),
                "replayed": True,
            }
        raffle = db.scalar(select(Raffle).where(Raffle.id == raffle_id).with_for_update())
        if raffle is None:
            raise HTTPException(status_code=404, detail="Tirage introuvable.")
        now = datetime.now(UTC)
        opening = (
            raffle.date_ouverture.replace(tzinfo=UTC)
            if raffle.date_ouverture.tzinfo is None
            else raffle.date_ouverture
        )
        drawing = (
            raffle.date_tirage.replace(tzinfo=UTC)
            if raffle.date_tirage.tzinfo is None
            else raffle.date_tirage
        )
        if raffle.statut != "OUVERT" or now < opening or now >= drawing:
            raise HTTPException(
                status_code=409, detail="Les inscriptions à ce tirage sont fermées."
            )
        txn = apply_points_change(
            db,
            user_id=user.id,
            amount=-ENTRY_COST,
            type="RAFFLE_ENTRY",
            idempotency_key=f"raffle-entry:{raffle_id}",
            now=now,
        )
        participation = RaffleTicket(
            id=str(uuid4()), raffle_id=raffle_id, user_id=user.id, created_at=now
        )
        db.add(participation)
        db.flush()
        db.commit()
        return {
            "id": participation.id,
            "raffleId": raffle_id,
            "coutPoints": ENTRY_COST,
            "soldePoints": txn.balance_after,
            "createdAt": now.isoformat(),
            "replayed": False,
        }
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Une participation à ce tirage existe déjà."
        ) from error
    except Exception:
        db.rollback()
        raise


@viewer_router.get("/raffle-tickets")
def own_raffle_tickets(
    request: Request,
    db: DatabaseSession,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    user = _current_user(request, db)
    where = RaffleTicket.user_id == user.id
    rows = list(
        db.execute(
            select(RaffleTicket, Raffle)
            .join(Raffle)
            .where(where)
            .order_by(RaffleTicket.created_at.desc(), RaffleTicket.id.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    )
    total = db.scalar(select(func.count()).select_from(RaffleTicket).where(where)) or 0
    values = []
    for ticket, raffle in rows:
        winner = db.scalar(select(RaffleWinner).where(RaffleWinner.raffle_ticket_id == ticket.id))
        lot = db.get(RaffleLot, winner.lot_id) if winner else None
        values.append(
            {
                "id": ticket.id,
                "raffleId": raffle.id,
                "raffleTitre": raffle.titre,
                "createdAt": ticket.created_at.isoformat(),
                "statut": raffle.statut,
                "gagnant": winner is not None,
                "lot": {"id": lot.id, "nom": lot.nom} if lot else None,
            }
        )
    return {"tickets": values, **_pages(total, page, limit)}


@public_router.get("/raffles/{raffle_id}/result")
def raffle_result(raffle_id: str, db: DatabaseSession):
    raffle = db.scalar(select(Raffle).where(Raffle.id == raffle_id))
    if raffle is None:
        raise HTTPException(status_code=404, detail="Tirage introuvable.")
    if raffle.statut != "TIRE":
        raise HTTPException(
            status_code=404, detail="Le résultat de ce tirage n'est pas encore publié."
        )
    winners = list(
        db.execute(
            select(RaffleWinner, RaffleTicket, RaffleLot, User)
            .join(RaffleTicket, RaffleWinner.raffle_ticket_id == RaffleTicket.id)
            .join(RaffleLot, RaffleWinner.lot_id == RaffleLot.id)
            .join(User, RaffleTicket.user_id == User.id)
            .where(RaffleWinner.raffle_id == raffle_id)
            .order_by(RaffleWinner.rank)
        )
    )
    return {
        "id": raffle.id,
        "titre": raffle.titre,
        "statut": raffle.statut,
        "dateTirage": raffle.date_tirage.isoformat(),
        "resultatPublieAt": raffle.resultat_publie_at.isoformat()
        if raffle.resultat_publie_at
        else None,
        "graineAleatoire": raffle.graine_aleatoire,
        "empreinteParticipants": raffle.empreinte_participants,
        "nombreParticipants": raffle.nombre_participants,
        "gagnants": [
            {
                "rang": w.rank,
                "lotId": lot.id,
                "lotNom": lot.nom,
                "ticketId": ticket.id,
                "pseudo": user.pseudo,
            }
            for w, ticket, lot, user in winners
        ],
    }


@public_router.get("/raffles/{raffle_id}/participants")
def raffle_participants(
    raffle_id: str,
    db: DatabaseSession,
    page: int = Query(default=0, ge=0),
    taille: int = Query(default=500, ge=1, le=2000),
):
    raffle = db.get(Raffle, raffle_id)
    if raffle is None:
        raise HTTPException(status_code=404, detail="Tirage introuvable.")
    if raffle.statut != "TIRE":
        raise HTTPException(status_code=404, detail="La liste est publiée après le tirage.")
    ids = list(
        db.scalars(
            select(RaffleTicket.id)
            .where(RaffleTicket.raffle_id == raffle_id)
            .order_by(RaffleTicket.id)
            .offset(page * taille)
            .limit(taille)
        )
    )
    return {
        "id": raffle_id,
        "empreinteParticipants": raffle.empreinte_participants,
        "nombreParticipants": raffle.nombre_participants,
        "page": page,
        "taillePage": taille,
        "participants": sorted(ids),
    }


@admin_draw_router.post("/{raffle_id}/draw")
def execute_draw(raffle_id: str, payload: DrawInput, request: Request, db: DatabaseSession):
    _require_origin(request)
    admin = require_admin(request, db)
    enforce_admin_rate_limit(request, admin.id)
    try:
        raffle = db.scalar(select(Raffle).where(Raffle.id == raffle_id).with_for_update())
        if raffle is None:
            raise HTTPException(status_code=404, detail="Tirage introuvable.")
        if raffle.statut == "TIRE":
            audit = db.get(RaffleDrawAudit, raffle_id)
            incoming_commitment = hashlib.sha256(
                payload.graineExploitant.encode()
            ).hexdigest()
            if (
                audit is None
                or not hmac.compare_digest(incoming_commitment, audit.seed_commitment)
                or payload.entropiePublique != raffle.entropie_publique
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Les paramètres ne correspondent pas au tirage déjà effectué.",
                )
            stored = _stored_draw_result(db, raffle)
            db.rollback()
            return stored
        if raffle.statut != "OUVERT" or datetime.now(UTC) < (
            raffle.date_tirage.replace(tzinfo=UTC)
            if raffle.date_tirage.tzinfo is None
            else raffle.date_tirage
        ):
            raise HTTPException(status_code=409, detail="Le tirage n'est pas encore éligible.")
        commitment = hashlib.sha256(payload.graineExploitant.encode()).hexdigest()
        if not raffle.engagement_graine or commitment != raffle.engagement_graine.lower():
            raise HTTPException(
                status_code=409, detail="La graine ne correspond pas à l’engagement publié."
            )
        tickets = list(
            db.scalars(
                select(RaffleTicket)
                .where(RaffleTicket.raffle_id == raffle_id)
                .order_by(RaffleTicket.id)
                .with_for_update()
            )
        )
        lots = list(
            db.scalars(
                select(RaffleLot).where(RaffleLot.raffle_id == raffle_id).order_by(RaffleLot.id)
            )
        )
        if not lots:
            raise HTTPException(status_code=409, detail="Aucun lot n'est configuré pour ce tirage.")
        draw_seed = hashlib.sha256(
            f"{payload.graineExploitant}:{payload.entropiePublique}".encode()
        ).hexdigest()
        participant_hash = _canonical_hash([ticket.id for ticket in tickets])
        selected = _pick_winners(draw_seed, tickets, lots)
        result_rows = []
        for rank, (lot, ticket_id) in enumerate(selected, 1):
            winner = RaffleWinner(
                id=str(uuid4()),
                raffle_id=raffle_id,
                raffle_ticket_id=ticket_id,
                lot_id=lot.id,
                rank=rank,
            )
            db.add(winner)
            result_rows.append({"lotId": lot.id, "ticketId": ticket_id})
        now = datetime.now(UTC)
        raffle.statut = "TIRE"
        raffle.graine_aleatoire = draw_seed
        raffle.entropie_publique = payload.entropiePublique
        raffle.empreinte_participants = participant_hash
        raffle.nombre_participants = len(tickets)
        raffle.resultat_publie_at = now
        audit = RaffleDrawAudit(
            raffle_id=raffle_id,
            result_hash=hashlib.sha256(
                json.dumps(result_rows, separators=(",", ":")).encode()
            ).hexdigest(),
            seed_commitment=commitment,
            participants_hash=participant_hash,
            algorithm=DRAW_ALGORITHM,
            executed_by_id=admin.id,
            executed_at=now,
        )
        db.add(audit)
        db.add(
            AdminAuditEvent(
                id=str(uuid4()),
                actor_id=admin.id,
                action="RAFFLE_DRAW_EXECUTED",
                entity_type="Raffle",
                entity_id=raffle_id,
                metadata_json={"resultHash": audit.result_hash, "seedCommitment": commitment},
            )
        )
        db.flush()
        db.commit()
        # Raw draw result intentionally omits participant user IDs.
        return {
            "raffleId": raffle_id,
            "graineAleatoire": draw_seed,
            "empreinteParticipants": participant_hash,
            "resultatPublieAt": now.isoformat(),
            "nombreTickets": len(tickets),
            "gagnants": result_rows,
        }
    except Exception:
        db.rollback()
        raise

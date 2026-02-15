from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction as db_transaction
from django.db.models import Q
from django.utils import timezone

from voitures.models import Transaction, Voiture


@dataclass(frozen=True)
class PurchaseRequestResult:
    transaction: Transaction
    created: bool


class TransactionError(Exception):
    pass


def get_reservation_ttl_hours() -> int:
    ttl_hours = getattr(settings, "RESERVATION_TTL_HOURS", 24) or 24
    try:
        ttl_hours = int(ttl_hours)
    except (TypeError, ValueError):
        ttl_hours = 24
    return max(ttl_hours, 1)


def expire_stale_purchase_requests(*, ttl_hours: int | None = None) -> int:
    """
    Annule automatiquement les transactions 'en_attente' trop anciennes et libère
    les voitures réservées qui n'ont plus de demande active.
    """
    ttl = ttl_hours if ttl_hours is not None else get_reservation_ttl_hours()
    cutoff = timezone.now() - timedelta(hours=ttl)

    stale = Transaction.objects.filter(statut="en_attente", date_transaction__lt=cutoff)
    if not stale.exists():
        return 0

    car_ids = list(stale.values_list("voiture_id", flat=True).distinct())
    updated = stale.update(statut="annulee", date_mise_a_jour=timezone.now())

    if car_ids:
        Voiture.objects.filter(id__in=car_ids, est_reservee=True).exclude(
            transaction__statut="en_attente"
        ).update(est_reservee=False)

    return updated


def get_pending_transaction_for_user(*, voiture: Voiture, user: User) -> Transaction | None:
    return (
        Transaction.objects.filter(voiture=voiture, statut="en_attente")
        .filter(Q(acheteur=user) | Q(vendeur=user))
        .order_by("-date_transaction")
        .first()
    )


def create_purchase_request(*, voiture_id: int, buyer: User) -> PurchaseRequestResult:
    expire_stale_purchase_requests()

    with db_transaction.atomic():
        locked_voiture = Voiture.objects.select_for_update().select_related("vendeur").get(id=voiture_id)

        if locked_voiture.moderation_status != "approved":
            raise TransactionError("Cette annonce n'est pas encore validée.")

        if locked_voiture.est_vendue:
            raise TransactionError("Cette voiture n'est plus disponible.")

        existing = Transaction.objects.filter(
            voiture=locked_voiture, statut="en_attente", acheteur=buyer
        ).first()
        if existing:
            return PurchaseRequestResult(transaction=existing, created=False)

        if locked_voiture.est_reservee:
            raise TransactionError("Cette voiture est déjà réservée.")

        trx = Transaction.objects.create(
            voiture=locked_voiture,
            acheteur=buyer,
            vendeur=locked_voiture.vendeur,
            prix_final=locked_voiture.prix,
            statut="en_attente",
        )

        locked_voiture.est_reservee = True
        locked_voiture.save(update_fields=["est_reservee"])

    return PurchaseRequestResult(transaction=trx, created=True)


def cancel_purchase_request(*, transaction_id: int, buyer: User) -> Transaction:
    expire_stale_purchase_requests()

    trx = Transaction.objects.select_related("voiture", "vendeur").get(
        id=transaction_id, acheteur=buyer, statut="en_attente"
    )

    with db_transaction.atomic():
        locked = Voiture.objects.select_for_update().get(id=trx.voiture_id)
        Transaction.objects.filter(id=trx.id, statut="en_attente").update(
            statut="annulee", date_mise_a_jour=timezone.now()
        )
        if not Transaction.objects.filter(voiture=locked, statut="en_attente").exists():
            locked.est_reservee = False
            locked.save(update_fields=["est_reservee"])

    trx.refresh_from_db()
    return trx


def refuse_purchase_request(*, transaction_id: int, seller: User) -> Transaction:
    expire_stale_purchase_requests()

    trx = Transaction.objects.select_related("voiture", "acheteur").get(
        id=transaction_id, vendeur=seller, statut="en_attente"
    )

    with db_transaction.atomic():
        locked = Voiture.objects.select_for_update().get(id=trx.voiture_id)
        Transaction.objects.filter(id=trx.id, statut="en_attente").update(
            statut="annulee", date_mise_a_jour=timezone.now()
        )
        if not Transaction.objects.filter(voiture=locked, statut="en_attente").exists():
            locked.est_reservee = False
            locked.save(update_fields=["est_reservee"])

    trx.refresh_from_db()
    return trx


def confirm_sale(*, transaction_id: int, seller: User) -> Transaction:
    expire_stale_purchase_requests()

    trx = Transaction.objects.select_related("voiture", "acheteur").get(
        id=transaction_id, vendeur=seller, statut="en_attente"
    )

    with db_transaction.atomic():
        locked = Voiture.objects.select_for_update().get(id=trx.voiture_id)

        now = timezone.now()
        Transaction.objects.filter(id=trx.id, statut="en_attente").update(
            statut="confirmee",
            date_confirmation=now,
            date_mise_a_jour=now,
        )
        locked.est_vendue = True
        locked.est_reservee = False
        locked.save(update_fields=["est_vendue", "est_reservee"])

        Transaction.objects.filter(voiture=locked, statut="en_attente").exclude(id=trx.id).update(
            statut="annulee", date_mise_a_jour=now
        )

    trx.refresh_from_db()
    return trx

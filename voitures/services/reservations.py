from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.db import transaction as db_transaction
from django.utils import timezone

from voitures.models import Reservation, Voiture


def _ttl_hours() -> int:
    val = getattr(settings, "RESERVATION_TTL_HOURS", 24) or 24
    try:
        return max(int(val), 1)
    except (TypeError, ValueError):
        return 24


def expire_finished_reservations() -> int:
    """Marque terminées les réservations passées et libère la voiture."""
    now = timezone.now()
    finished = Reservation.objects.filter(
        statut__in=["en_attente", "acceptee"], fin__lt=now
    )
    ids = list(finished.values_list("id", flat=True))
    count = finished.update(statut="terminee")
    if ids:
        car_ids = Reservation.objects.filter(id__in=ids).values_list("voiture_id", flat=True)
        Voiture.objects.filter(id__in=car_ids, est_reservee=True).update(est_reservee=False)
    return count


def expire_stale_pending() -> int:
    """Annule les réservations en attente trop anciennes (TTL)."""
    cutoff = timezone.now() - timedelta(hours=_ttl_hours())
    stale = Reservation.objects.filter(statut="en_attente", date_creation__lt=cutoff)
    ids = list(stale.values_list("id", flat=True))
    count = stale.update(statut="annulee")
    if ids:
        car_ids = Reservation.objects.filter(id__in=ids).values_list("voiture_id", flat=True)
        Voiture.objects.filter(id__in=car_ids, est_reservee=True).update(est_reservee=False)
    return count


def create_reservation(*, voiture_id: int, client, debut, fin, type: str, note: str, signature: str) -> Reservation:
    expire_finished_reservations()
    expire_stale_pending()

    if debut >= fin:
        raise ValueError("Créneau invalide (début >= fin)")

    with db_transaction.atomic():
        car = Voiture.objects.select_for_update().get(id=voiture_id, est_vendue=False)

        # Conflits avec transactions d'achat
        if car.est_reservee:
            raise ValueError("Cette voiture est déjà réservée")

        if Reservation.overlaps(voiture_id=car.id, start=debut, end=fin):
            raise ValueError("Ce créneau est indisponible")

        res = Reservation.objects.create(
            voiture=car,
            client=client,
            type=type,
            debut=debut,
            fin=fin,
            note=note,
            signature=signature,
        )

        car.est_reservee = True
        car.save(update_fields=["est_reservee"])

    return res


def update_status(*, reservation_id: int, user, new_status: str) -> Reservation:
    if new_status not in {"acceptee", "refusee", "annulee"}:
        raise ValueError("Statut invalide")

    with db_transaction.atomic():
        res = Reservation.objects.select_for_update().select_related("voiture").get(id=reservation_id)

        if res.voiture.vendeur != user and res.client != user:
            raise PermissionError("Non autorisé")

        res.statut = new_status
        res.save(update_fields=["statut", "date_creation"])

        if new_status in {"refusee", "annulee"}:
            # Libérer la voiture si plus aucune réservation active
            if not Reservation.overlaps(res.voiture_id, res.debut, res.fin):
                res.voiture.est_reservee = False
                res.voiture.save(update_fields=["est_reservee"])

    return res

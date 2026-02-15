from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from voitures.models import Location, Voiture


def expire_finished_locations() -> int:
    """Passe en terminée les locations finies et libère la voiture."""
    now = timezone.now()
    finished = Location.objects.filter(statut__in=["a_venir", "en_cours"], fin__lt=now)
    ids = list(finished.values_list("id", flat=True))
    count = finished.update(statut="terminee")
    if ids:
        car_ids = Location.objects.filter(id__in=ids).values_list("voiture_id", flat=True)
        Voiture.objects.filter(id__in=car_ids, est_louee=True).update(est_louee=False, est_reservee=False)
    return count


def start_due_locations() -> int:
    """Passe en cours les locations qui démarrent maintenant."""
    now = timezone.now()
    due = Location.objects.filter(statut="a_venir", debut__lte=now, fin__gt=now)
    ids = list(due.values_list("id", flat=True))
    count = due.update(statut="en_cours")
    if ids:
        car_ids = Location.objects.filter(id__in=ids).values_list("voiture_id", flat=True)
        Voiture.objects.filter(id__in=car_ids).update(est_louee=True, est_reservee=True)
    return count


def create_location(*, voiture_id: int, client, debut, fin, prix_total=None, conditions="") -> Location:
    if debut >= fin:
        raise ValueError("Créneau invalide (début >= fin)")

    expire_finished_locations()
    start_due_locations()

    with transaction.atomic():
        car = Voiture.objects.select_for_update().get(id=voiture_id, est_vendue=False)
        if car.est_louee:
            raise ValueError("Véhicule déjà loué.")
        if Location.overlaps(voiture_id=car.id, start=debut, end=fin):
            raise ValueError("Créneau indisponible.")

        loc = Location.objects.create(
            voiture=car,
            client=client,
            debut=debut,
            fin=fin,
            prix_total=prix_total,
            conditions=conditions,
        )
        car.est_louee = True
        car.est_reservee = True
        car.save(update_fields=["est_louee", "est_reservee"])
    return loc


def current_status(voiture: Voiture):
    """Renvoie un dict de statut location/disponibilité."""
    now = timezone.now()
    active = Location.objects.filter(
        voiture=voiture, statut="en_cours", debut__lte=now, fin__gt=now
    ).order_by("fin").first()
    upcoming = (
        Location.objects.filter(voiture=voiture, statut="a_venir", debut__gte=now)
        .order_by("debut")
        .first()
    )
    return {
        "est_louee": bool(active),
        "en_cours": active,
        "prochaine": upcoming,
        "disponible": not active and not voiture.est_vendue and not voiture.est_reservee,
        "etat": "louee" if active else ("reservee" if voiture.est_reservee else "disponible"),
    }


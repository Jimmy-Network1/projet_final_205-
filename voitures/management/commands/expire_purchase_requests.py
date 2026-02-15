from __future__ import annotations

from django.core.management.base import BaseCommand

from voitures.services.transactions import expire_stale_purchase_requests, get_reservation_ttl_hours


class Command(BaseCommand):
    help = "Annule les demandes d'achat en attente expirées et libère les réservations."

    def add_arguments(self, parser):
        parser.add_argument(
            "--ttl-hours",
            type=int,
            default=None,
            help="Override RESERVATION_TTL_HOURS (en heures).",
        )

    def handle(self, *args, **options):
        ttl_hours = options.get("ttl_hours")
        if ttl_hours is None:
            ttl_hours = get_reservation_ttl_hours()

        count = expire_stale_purchase_requests(ttl_hours=ttl_hours)
        self.stdout.write(self.style.SUCCESS(f"Expirées: {count} (ttl={ttl_hours}h)"))

from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand

from voitures.models import Marque


class Command(BaseCommand):
    help = "Initialise un catalogue minimal de marques (utile si la base est vide)."

    DEFAULT_MARQUES: list[dict] = [
        {"nom": "Peugeot", "pays": "France", "date_creation": date(1810, 1, 1)},
        {"nom": "Renault", "pays": "France", "date_creation": date(1899, 1, 1)},
        {"nom": "Citroën", "pays": "France", "date_creation": date(1919, 1, 1)},
        {"nom": "Toyota", "pays": "Japon", "date_creation": date(1937, 1, 1)},
        {"nom": "Honda", "pays": "Japon", "date_creation": date(1948, 1, 1)},
        {"nom": "Nissan", "pays": "Japon", "date_creation": date(1933, 1, 1)},
        {"nom": "Volkswagen", "pays": "Allemagne", "date_creation": date(1937, 1, 1)},
        {"nom": "BMW", "pays": "Allemagne", "date_creation": date(1916, 1, 1)},
        {"nom": "Mercedes-Benz", "pays": "Allemagne", "date_creation": date(1926, 1, 1)},
        {"nom": "Audi", "pays": "Allemagne", "date_creation": date(1909, 1, 1)},
        {"nom": "Ford", "pays": "États-Unis", "date_creation": date(1903, 1, 1)},
        {"nom": "Tesla", "pays": "États-Unis", "date_creation": date(2003, 1, 1)},
        {"nom": "Hyundai", "pays": "Corée du Sud", "date_creation": date(1967, 1, 1)},
        {"nom": "Kia", "pays": "Corée du Sud", "date_creation": date(1944, 1, 1)},
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Ajoute les marques manquantes même si la base n'est pas vide.",
        )

    def handle(self, *args, **options):
        force: bool = bool(options.get("force"))

        if Marque.objects.exists() and not force:
            self.stdout.write(self.style.SUCCESS("Catalogue déjà initialisé (marques existantes)."))
            self.stdout.write("Utilisez --force pour ajouter les marques manquantes.")
            return

        created = 0
        for item in self.DEFAULT_MARQUES:
            _, was_created = Marque.objects.get_or_create(
                nom=item["nom"],
                defaults={
                    "pays": item["pays"],
                    "date_creation": item["date_creation"],
                    "description": "",
                },
            )
            created += 1 if was_created else 0

        total = Marque.objects.count()
        self.stdout.write(self.style.SUCCESS(f"✓ Marques créées: {created}"))
        self.stdout.write(self.style.SUCCESS(f"✓ Total marques: {total}"))


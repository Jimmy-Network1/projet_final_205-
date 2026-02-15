from __future__ import annotations

import secrets

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée (ou met à jour) un compte superuser de manière idempotente."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="admin")
        parser.add_argument("--email", default="admin@example.com")
        parser.add_argument("--password", default=None)
        parser.add_argument(
            "--print-password",
            action="store_true",
            help="Affiche le mot de passe généré si aucun --password n'est fourni.",
        )

    def handle(self, *args, **options):
        username: str = options["username"]
        email: str = options["email"]
        password: str | None = options["password"]
        print_password: bool = bool(options["print_password"])

        if not password:
            password = secrets.token_urlsafe(18)
            if print_password:
                self.stdout.write(self.style.WARNING(f"Mot de passe généré: {password}"))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "Mot de passe généré (non affiché). Utilise --print-password pour l'afficher."
                    )
                )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        changed_fields: list[str] = []
        if user.email != email:
            user.email = email
            changed_fields.append("email")
        if not user.is_staff:
            user.is_staff = True
            changed_fields.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            changed_fields.append("is_superuser")
        if not user.is_active:
            user.is_active = True
            changed_fields.append("is_active")

        user.set_password(password)
        user.save(update_fields=changed_fields or None)

        if created:
            self.stdout.write(self.style.SUCCESS(f"Superuser créé: {username}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser mis à jour: {username}"))

from __future__ import annotations

import os
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from voitures.models import Marque


def _normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    return "".join(ch for ch in value if ch.isalnum())


@dataclass(frozen=True)
class Candidate:
    source: Path
    key: str
    ext: str


class Command(BaseCommand):
    help = "Importe des logos (fichiers) et les associe aux marques existantes."

    def add_arguments(self, parser):
        parser.add_argument(
            "source_dir",
            nargs="?",
            default="logo",
            help="Dossier qui contient les logos (par défaut: 'logo').",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait fait sans écrire de fichiers ni modifier la base.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Remplace un logo existant si déjà défini.",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"]).expanduser().resolve()
        dry_run: bool = options["dry_run"]
        overwrite: bool = options["overwrite"]

        if not source_dir.exists() or not source_dir.is_dir():
            raise CommandError(f"Dossier introuvable: {source_dir}")

        allowed_ext = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
        files = [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in allowed_ext]
        if not files:
            raise CommandError(f"Aucune image trouvée dans: {source_dir}")

        # Petites corrections courantes (typos, séparateurs)
        alias = {
            "bwm": "bmw",
            "pegeo": "peugeot",
            "mercedesbenz": "mercedesbenz",
            "mercedes_benz": "mercedesbenz",
            "mercedesbenzlogo": "mercedesbenz",
        }

        candidates: list[Candidate] = []
        for path in files:
            stem = path.stem.strip()
            key = _normalize_key(stem)
            key = alias.get(key, key)
            candidates.append(Candidate(source=path, key=key, ext=path.suffix.lower()))

        marques = list(Marque.objects.all())
        marque_by_key = {_normalize_key(m.nom): m for m in marques}
        # Alias côté DB (au cas où la marque est saisie différemment)
        for m in marques:
            if _normalize_key(m.nom) == "mercedesbenz":
                marque_by_key["mercedesbenz"] = m
        # Si la DB a "Citroën" ça matche déjà via normalisation.

        media_root = Path(settings.MEDIA_ROOT)
        dest_dir = media_root / "logos"
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)

        matched = 0
        skipped = 0
        missing = []

        for c in sorted(candidates, key=lambda x: x.source.name.lower()):
            marque = marque_by_key.get(c.key)
            if not marque:
                missing.append(c.source.name)
                continue

            if marque.logo and not overwrite:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"SKIP {marque.nom}: logo déjà défini"))
                continue

            safe_name = f"{_normalize_key(marque.nom)}{c.ext}"
            dest_path = dest_dir / safe_name
            relative = os.path.join("logos", safe_name)

            self.stdout.write(f"SET  {marque.nom} <- {c.source.name}  =>  {relative}")

            if not dry_run:
                shutil.copy2(c.source, dest_path)
                marque.logo.name = relative
                marque.save(update_fields=["logo"])

            matched += 1

        if missing:
            self.stdout.write(self.style.WARNING("Fichiers non associés (aucune marque correspondante):"))
            for name in missing:
                self.stdout.write(self.style.WARNING(f" - {name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé. Liés: {matched}, ignorés: {skipped}, non associés: {len(missing)}"
            )
        )

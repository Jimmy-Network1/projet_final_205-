from __future__ import annotations

import os
import shutil
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import User

from voitures.models import Marque, Modele, Voiture


def _normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    return "".join(ch for ch in value if ch.isalnum())


@dataclass(frozen=True)
class ImageFile:
    source: Path
    key: str
    ext: str


class Command(BaseCommand):
    help = "Importe des images de véhicules et les associe aux annonces existantes selon le nom du fichier."

    def add_arguments(self, parser):
        parser.add_argument(
            "source_dir",
            nargs="?",
            default=os.path.join("LES IMAGES", "VOITURE"),
            help="Dossier qui contient les images (par défaut: 'LES IMAGES/VOITURE').",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait fait sans écrire de fichiers ni modifier la base.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Remplace l'image principale même si elle est déjà définie.",
        )
        parser.add_argument(
            "--create-missing",
            action="store_true",
            help="Crée une annonce de démo si aucune voiture ne correspond à l'image (ex: 'TESLA.jpg').",
        )

    def handle(self, *args, **options):
        source_dir = Path(options["source_dir"]).expanduser().resolve()
        dry_run: bool = options["dry_run"]
        overwrite: bool = options["overwrite"]
        create_missing: bool = options["create_missing"]

        if not source_dir.exists() or not source_dir.is_dir():
            raise CommandError(f"Dossier introuvable: {source_dir}")

        allowed_ext = {".png", ".jpg", ".jpeg", ".webp"}
        files = [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in allowed_ext]
        if not files:
            raise CommandError(f"Aucune image trouvée dans: {source_dir}")

        alias = {
            "bwm": "bmw",
            "pegeo": "peugeot",
        }

        image_files: list[ImageFile] = []
        for path in files:
            key = alias.get(_normalize_key(path.stem), _normalize_key(path.stem))
            image_files.append(ImageFile(source=path, key=key, ext=path.suffix.lower()))

        voitures = list(Voiture.objects.select_related("modele__marque").order_by("id"))
        if not voitures and not create_missing:
            raise CommandError("Aucune voiture en base. Ajoutez des annonces ou utilisez --create-missing.")

        # Indexes for matching.
        by_full_key: dict[str, list[Voiture]] = {}
        by_marque_key: dict[str, list[Voiture]] = {}
        by_modele_key: dict[str, list[Voiture]] = {}

        for v in voitures:
            marque = v.modele.marque.nom
            modele = v.modele.nom
            full_key = _normalize_key(f"{marque}{modele}")
            marque_key = _normalize_key(marque)
            modele_key = _normalize_key(modele)
            by_full_key.setdefault(full_key, []).append(v)
            by_marque_key.setdefault(marque_key, []).append(v)
            by_modele_key.setdefault(modele_key, []).append(v)

        marque_by_key = {_normalize_key(m.nom): m for m in Marque.objects.all()}

        media_root = Path(settings.MEDIA_ROOT)
        dest_dir = media_root / "voitures"
        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)

        def should_skip(v: Voiture) -> bool:
            if overwrite:
                return False
            # Consider default image as "missing"
            return bool(v.image_principale) and v.image_principale.name not in {"", "voitures/default.jpg"}

        linked = 0
        skipped = 0
        unmatched = []

        default_model_by_marque = {
            "citroen": "C3",
            "tesla": "Model 3",
            "toyota": "Corolla",
            "volkswagen": "Golf",
            "ford": "Focus",
            "mercedesbenz": "Classe A",
            "bmw": "Série 3",
            "peugeot": "208",
            "renault": "Clio",
        }

        def ensure_demo_voiture_for_marque(marque_key: str) -> Voiture | None:
            marque = marque_by_key.get(marque_key)
            if not marque:
                return None
            vendeur = User.objects.filter(is_superuser=True).first() or User.objects.first()
            if not vendeur:
                raise CommandError("Aucun utilisateur en base. Créez un utilisateur avant --create-missing.")

            modele_nom = default_model_by_marque.get(marque_key, "Modèle")
            modele, _ = Modele.objects.get_or_create(
                marque=marque,
                nom=modele_nom,
                defaults={
                    "annee_lancement": 2015,
                    "type_carburant": "essence",
                    "transmission": "manuelle",
                    "puissance": 110,
                    "consommation": 6.0,
                },
            )
            voiture = Voiture.objects.create(
                modele=modele,
                prix=19990,
                kilometrage=45000,
                annee=2020,
                couleur="gris",
                etat="occasion",
                description="Annonce de démonstration (photo importée).",
                vendeur=vendeur,
            )
            return voiture

        for img in sorted(image_files, key=lambda x: x.source.name.lower()):
            targets: list[Voiture] = []

            if img.key in by_full_key:
                targets = by_full_key[img.key]
            elif img.key in by_marque_key:
                targets = by_marque_key[img.key]
            elif img.key in by_modele_key and len(by_modele_key[img.key]) == 1:
                targets = by_modele_key[img.key]

            if not targets:
                if create_missing and img.key in marque_by_key:
                    created = ensure_demo_voiture_for_marque(img.key)
                    if created:
                        # update indexes for this session
                        by_marque_key.setdefault(img.key, []).append(created)
                        targets = [created]
                if not targets:
                    unmatched.append(img.source.name)
                    continue

            for v in targets:
                if should_skip(v):
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"SKIP voiture#{v.id}: image déjà définie"))
                    continue

                marque_key = _normalize_key(v.modele.marque.nom)
                modele_key = _normalize_key(v.modele.nom)
                dest_name = f"{marque_key}_{modele_key}_{v.id}{img.ext}"
                dest_path = dest_dir / dest_name
                relative = os.path.join("voitures", dest_name)

                self.stdout.write(
                    f"SET  voiture#{v.id} ({v.modele.marque.nom} {v.modele.nom}) <- {img.source.name}  =>  {relative}"
                )

                if not dry_run:
                    shutil.copy2(img.source, dest_path)
                    v.image_principale.name = relative
                    v.save(update_fields=["image_principale"])

                linked += 1

        if unmatched:
            self.stdout.write(self.style.WARNING("Fichiers non associés (aucune voiture correspondante):"))
            for name in unmatched:
                self.stdout.write(self.style.WARNING(f" - {name}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Terminé. Liés: {linked}, ignorés: {skipped}, non associés: {len(unmatched)}"
            )
        )

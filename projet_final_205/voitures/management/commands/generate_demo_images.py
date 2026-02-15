from __future__ import annotations

import unicodedata
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from voitures.models import Voiture


def _normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    return "".join(ch for ch in value if ch.isalnum() or ch in {"-", "_"})


class Command(BaseCommand):
    help = "Génère des images de démo pour les annonces (utile en hébergement sans stockage persistant)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Remplace l'image même si elle est déjà définie.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Limite le nombre d'images générées (0 = aucune limite).",
        )

    def handle(self, *args, **options):
        overwrite: bool = options["overwrite"]
        limit: int = options["limit"] or 0

        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception as exc:  # pragma: no cover
            raise SystemExit(
                "Pillow est requis pour générer des images (pip install -r requirements.txt)."
            ) from exc

        media_root = Path(settings.MEDIA_ROOT)
        dest_dir = media_root / "voitures"
        dest_dir.mkdir(parents=True, exist_ok=True)

        def _load_font(size: int):
            try:
                return ImageFont.truetype("DejaVuSans.ttf", size=size)
            except Exception:
                return ImageFont.load_default()

        title_font = _load_font(62)
        subtitle_font = _load_font(36)
        meta_font = _load_font(32)

        qs = Voiture.objects.select_related("modele__marque").order_by("id")
        if limit > 0:
            qs = qs[:limit]

        generated = 0
        skipped = 0

        for v in qs:
            current = getattr(v.image_principale, "name", "") or ""
            is_missing = not current or current == "voitures/default.jpg"
            if not overwrite and not is_missing:
                skipped += 1
                continue

            marque = v.modele.marque.nom
            modele = v.modele.nom
            title = f"{marque} {modele}"

            year = getattr(v, "annee", "") or ""
            km = getattr(v, "kilometrage", "") or ""
            price = getattr(v, "prix_format", None)
            price_text = v.prix_format() if callable(price) else ""

            filename = f"demo_{_normalize_key(marque)}_{_normalize_key(modele)}_{v.id}.jpg"
            relative = f"voitures/{filename}"
            dest_path = dest_dir / filename

            width, height = 1200, 675
            image = Image.new("RGB", (width, height), color=(245, 247, 250))
            draw = ImageDraw.Draw(image)

            # Card background
            draw.rounded_rectangle(
                (60, 60, width - 60, height - 60),
                radius=28,
                outline=(220, 225, 235),
                width=6,
                fill=(255, 255, 255),
            )

            # Accent band
            draw.rounded_rectangle(
                (60, 60, width - 60, 190),
                radius=28,
                fill=(30, 55, 120),
            )

            # Title/subtitle
            draw.text((110, 90), "AutoMarket", fill=(230, 238, 255), font=subtitle_font)
            draw.text((110, 230), title, fill=(30, 45, 70), font=title_font)

            meta = f"{year}  •  {km} km"
            if price_text:
                meta = f"{meta}  •  {price_text}"
            draw.text((110, 320), meta, fill=(90, 105, 125), font=meta_font)

            # Simple car-like line
            line_color = (80, 125, 255)
            draw.line((250, 470, 430, 390, 770, 390, 950, 470), fill=line_color, width=14)
            draw.ellipse((320, 470, 440, 590), outline=line_color, width=14)
            draw.ellipse((760, 470, 880, 590), outline=line_color, width=14)

            image.save(dest_path, format="JPEG", quality=88, optimize=True)

            v.image_principale.name = relative
            v.save(update_fields=["image_principale"])
            generated += 1

        self.stdout.write(self.style.SUCCESS(f"Images générées: {generated}, ignorées: {skipped}"))


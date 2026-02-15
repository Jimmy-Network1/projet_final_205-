from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crée une image par défaut dans MEDIA_ROOT pour éviter les 404 sur voitures/default.jpg."

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        dest_dir = media_root / "voitures"
        dest_path = dest_dir / "default.jpg"

        if dest_path.exists():
            self.stdout.write(self.style.SUCCESS(f"OK: {dest_path} existe déjà"))
            return

        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception as exc:  # pragma: no cover
            raise SystemExit(
                "Pillow est requis pour générer l'image par défaut (pip install -r requirements.txt)."
            ) from exc

        width, height = 1200, 675
        image = Image.new("RGB", (width, height), color=(245, 247, 250))
        draw = ImageDraw.Draw(image)

        # Simple car-like line + title.
        line_color = (80, 125, 255)
        draw.rounded_rectangle(
            (70, 140, width - 70, height - 120),
            radius=24,
            outline=(220, 225, 235),
            width=6,
            fill=(255, 255, 255),
        )
        draw.line((220, 360, 450, 260, 760, 260, 980, 360), fill=line_color, width=14)
        draw.ellipse((300, 360, 420, 480), outline=line_color, width=14)
        draw.ellipse((780, 360, 900, 480), outline=line_color, width=14)

        title = "AutoMarket"
        subtitle = "Photo à venir"

        def _load_font(size: int):
            try:
                return ImageFont.truetype("DejaVuSans.ttf", size=size)
            except Exception:
                return ImageFont.load_default()

        title_font = _load_font(64)
        subtitle_font = _load_font(40)

        draw.text((120, 70), title, fill=(30, 45, 70), font=title_font)
        draw.text((120, 520), subtitle, fill=(120, 130, 150), font=subtitle_font)

        image.save(dest_path, format="JPEG", quality=88, optimize=True)
        self.stdout.write(self.style.SUCCESS(f"Créé: {dest_path}"))


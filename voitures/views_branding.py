from __future__ import annotations

import hashlib
import html
import mimetypes
import unicodedata
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse
from django.http.response import FileResponse

from voitures.models import Marque


def _brand_initials(name: str) -> str:
    cleaned = " ".join((name or "").strip().split())
    if not cleaned:
        return "?"
    parts = [p for p in cleaned.replace("-", " ").split(" ") if p]
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][:1] + parts[1][:1]).upper()


def _brand_colors(key: str) -> tuple[str, str]:
    digest = hashlib.sha256((key or "").encode("utf-8")).hexdigest()
    # Couleurs cohérentes par marque (mais sans liste hardcodée).
    hue = int(digest[:6], 16) % 360
    hue2 = (hue + 24) % 360
    return (f"hsl({hue} 82% 50%)", f"hsl({hue2} 86% 58%)")


def _normalize_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower()
    return "".join(ch for ch in value if ch.isalnum())


def _find_catalog_logo_path(*, catalog_dir: Path, marque_name: str) -> Path | None:
    if not catalog_dir.exists() or not catalog_dir.is_dir():
        return None

    wanted = _normalize_key(marque_name)
    if not wanted:
        return None

    alias = {
        "bwm": "bmw",
        "pegeo": "peugeot",
        "mercedes_benz": "mercedesbenz",
        "mercedesbenzlogo": "mercedesbenz",
    }
    wanted = alias.get(wanted, wanted)

    # Scan léger (quelques fichiers): match sur le "stem" normalisé.
    for file_path in sorted(catalog_dir.iterdir(), key=lambda p: p.name.lower()):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            continue
        stem_key = _normalize_key(file_path.stem)
        stem_key = alias.get(stem_key, stem_key)
        if stem_key == wanted:
            return file_path
    return None


def _file_response(path: Path) -> FileResponse:
    content_type, _ = mimetypes.guess_type(path.name)
    resp = FileResponse(path.open("rb"), content_type=content_type or "application/octet-stream")
    resp["Cache-Control"] = "public, max-age=86400"
    return resp


def marque_logo(request, marque_id: int):
    """
    Retourne le meilleur logo disponible pour une marque (fichier uploadé ou catalogue ./logo),
    avec fallback SVG si nécessaire.
    """
    try:
        marque = Marque.objects.only("id", "nom", "logo").get(id=marque_id)
    except Marque.DoesNotExist as exc:
        raise Http404 from exc

    # 1) Logo uploadé via Marque.logo
    logo = getattr(marque, "logo", None)
    if logo and getattr(logo, "name", ""):
        try:
            content_type, _ = mimetypes.guess_type(logo.name)
            resp = FileResponse(logo.open("rb"), content_type=content_type or "application/octet-stream")
            resp["Cache-Control"] = "public, max-age=86400"
            return resp
        except Exception:
            pass

    # 2) Catalogue (dossier ./logo par défaut)
    catalog_dir = Path(getattr(settings, "BRAND_LOGO_CATALOG_DIR", settings.BASE_DIR / "logo"))
    found = _find_catalog_logo_path(catalog_dir=catalog_dir, marque_name=marque.nom or "")
    if found:
        return _file_response(found)

    # 3) Fallback SVG généré
    return marque_logo_svg(request, marque_id)


def marque_logo_svg(request, marque_id: int):
    """
    Logo de fallback (SVG) pour une marque.
    Utile quand aucun fichier `Marque.logo` n'est défini, ou en cas de 404 média.
    """
    try:
        marque = Marque.objects.only("id", "nom").get(id=marque_id)
    except Marque.DoesNotExist as exc:
        raise Http404 from exc

    name = (marque.nom or "").strip() or "Marque"
    initials = _brand_initials(name)
    c1, c2 = _brand_colors(name)

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="160" height="80" viewBox="0 0 160 80" role="img" aria-label="{html.escape(name)}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/>
      <stop offset="1" stop-color="{c2}"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="159" height="79" rx="16" fill="url(#g)" stroke="rgba(15,23,42,0.10)"/>
  <text x="80" y="48" text-anchor="middle" font-family="Inter,system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif"
        font-size="30" font-weight="700" fill="rgba(255,255,255,0.96)" letter-spacing="0.5">{html.escape(initials)}</text>
</svg>
"""

    resp = HttpResponse(svg, content_type="image/svg+xml; charset=utf-8")
    resp["Cache-Control"] = "public, max-age=86400"
    return resp

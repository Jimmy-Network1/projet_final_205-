from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.utils import timezone

from voitures.models import Transaction
from voitures.services.simple_pdf import PdfCanvas, build_one_page_pdf, estimate_text_width


def _user_label(user) -> str:
    if not user:
        return "—"
    name = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
    if not name:
        name = user.username
    email = (user.email or "").strip()
    if email:
        return f"{name} ({email})"
    return name


def _user_name(user) -> str:
    if not user:
        return "—"
    full = f"{(user.first_name or '').strip()} {(user.last_name or '').strip()}".strip()
    return full or getattr(user, "username", "—") or "—"


def _user_contact(user) -> str:
    if not user:
        return "—"
    email = (getattr(user, "email", "") or "").strip()
    return email or "—"


def _format_fcfa(amount) -> str:
    if amount is None:
        return "—"
    try:
        dec = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        return f"{amount} FCFA"

    sign = "-" if dec < 0 else ""
    dec = abs(dec).quantize(Decimal("0.01"))
    int_part, frac_part = f"{dec:.2f}".split(".")
    groups: list[str] = []
    while int_part:
        groups.append(int_part[-3:])
        int_part = int_part[:-3]
    grouped = " ".join(reversed(groups)) or "0"
    return f"{sign}{grouped},{frac_part} FCFA"


def _truncate(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return "…"
    return text[: max_chars - 1].rstrip() + "…"


def _draw_text_right(
    canvas: PdfCanvas,
    *,
    x_right: float,
    y: float,
    text: str,
    font: str,
    size: float,
    color: tuple[float, float, float],
) -> None:
    width = estimate_text_width(text, font=font, size=size)
    canvas.text(x_right - width, y, text, font=font, size=size, color=color)


def _draw_text_center(
    canvas: PdfCanvas,
    *,
    x_center: float,
    y: float,
    text: str,
    font: str,
    size: float,
    color: tuple[float, float, float],
) -> None:
    width = estimate_text_width(text, font=font, size=size)
    canvas.text(x_center - (width / 2.0), y, text, font=font, size=size, color=color)


def build_transaction_receipt(*, transaction: Transaction, role: str) -> bytes:
    voiture = transaction.voiture
    modele = getattr(voiture, "modele", None)
    marque = getattr(modele, "marque", None)

    confirmation = transaction.date_confirmation or transaction.date_mise_a_jour or transaction.date_transaction
    if timezone.is_naive(confirmation):
        confirmation = timezone.make_aware(confirmation)

    filename = f"recu_transaction_{transaction.id}_{role}.pdf"

    tz = timezone.get_current_timezone()
    confirmation_str = confirmation.astimezone(tz).strftime("%d/%m/%Y %H:%M")
    statut = (transaction.get_statut_display_fr() or "").strip() or "—"

    # Couleurs (RGB 0..1)
    BLUE = (0.07, 0.36, 0.83)
    BLUE_DARK = (0.05, 0.25, 0.62)
    TEXT = (0.10, 0.12, 0.16)
    MUTED = (0.38, 0.42, 0.50)
    BORDER = (0.86, 0.89, 0.93)
    LIGHT = (0.97, 0.98, 0.99)
    WHITE = (1.0, 1.0, 1.0)

    status_color = (0.18, 0.63, 0.34)  # vert
    if transaction.statut == "terminee":
        status_color = (0.05, 0.60, 0.64)  # bleu-vert

    canvas = PdfCanvas()

    # Page
    PAGE_W, PAGE_H = 612.0, 792.0
    M = 36.0
    X = M
    W = PAGE_W - 2 * M
    Y_TOP = PAGE_H - M

    # 1) En-tête
    banner_h = 54.0
    canvas.save()
    canvas.set_fill_color(*BLUE)
    canvas.rect(X, Y_TOP - banner_h, W, banner_h, stroke=False, fill=True)
    canvas.restore()

    # "Logo" minimal (monogramme)
    mark = 22.0
    canvas.save()
    canvas.set_fill_color(*BLUE_DARK)
    canvas.rect(X + 14.0, Y_TOP - 40.0, mark, mark, stroke=False, fill=True)
    canvas.restore()
    _draw_text_center(
        canvas,
        x_center=X + 14.0 + mark / 2.0,
        y=Y_TOP - 34.0,
        text="AM",
        font="F2",
        size=10.5,
        color=WHITE,
    )

    canvas.text(X + 14.0 + mark + 10.0, Y_TOP - 33.0, "AutoMarket", font="F2", size=18, color=WHITE)
    _draw_text_center(
        canvas,
        x_center=X + (W / 2.0),
        y=Y_TOP - 31.5,
        text="REÇU DE TRANSACTION",
        font="F2",
        size=13.5,
        color=WHITE,
    )

    # Ligne meta sous la bannière
    meta_h = 56.0
    meta_top = Y_TOP - banner_h - 12.0
    canvas.save()
    canvas.set_fill_color(*LIGHT)
    canvas.set_stroke_color(*BORDER)
    canvas.set_line_width(1.0)
    canvas.rect(X, meta_top - meta_h, W, meta_h, stroke=True, fill=True)
    canvas.restore()

    receipt_no = f"RECU-{transaction.id:06d}"
    canvas.text(X + 14.0, meta_top - 22.0, "Numéro du reçu", font="F1", size=9.5, color=MUTED)
    canvas.text(X + 14.0, meta_top - 38.0, receipt_no, font="F2", size=12.5, color=TEXT)

    mid_x = X + (W * 0.47)
    canvas.text(mid_x, meta_top - 22.0, "Date", font="F1", size=9.5, color=MUTED)
    canvas.text(mid_x, meta_top - 38.0, confirmation_str, font="F2", size=12.0, color=TEXT)

    # Statut (badge)
    badge_text = statut.upper()
    badge_w = max(110.0, estimate_text_width(badge_text, font="F2", size=10.5) + 26.0)
    badge_h = 22.0
    badge_x = X + W - 14.0 - badge_w
    badge_y = meta_top - 38.0
    canvas.save()
    canvas.set_fill_color(*status_color)
    canvas.rect(badge_x, badge_y, badge_w, badge_h, stroke=False, fill=True)
    canvas.restore()
    _draw_text_center(
        canvas,
        x_center=badge_x + badge_w / 2.0,
        y=badge_y + 6.2,
        text=badge_text,
        font="F2",
        size=10.5,
        color=WHITE,
    )

    # 2) Informations acheteur / vendeur
    section_y = meta_top - meta_h - 22.0
    box_gap = 12.0
    box_h = 96.0
    col_w = (W - box_gap) / 2.0
    left_x = X
    right_x = X + col_w + box_gap
    box_y = section_y - box_h

    for bx in (left_x, right_x):
        canvas.save()
        canvas.set_fill_color(*LIGHT)
        canvas.set_stroke_color(*BORDER)
        canvas.set_line_width(1.0)
        canvas.rect(bx, box_y, col_w, box_h, stroke=True, fill=True)
        canvas.restore()

    canvas.text(left_x + 14.0, section_y - 20.0, "ACHETEUR", font="F2", size=10.0, color=MUTED)
    canvas.text(right_x + 14.0, section_y - 20.0, "VENDEUR", font="F2", size=10.0, color=MUTED)

    buyer_name = _truncate(_user_name(transaction.acheteur), 38)
    buyer_contact = _truncate(_user_contact(transaction.acheteur), 44)
    seller_name = _truncate(_user_name(transaction.vendeur), 38)
    seller_contact = _truncate(_user_contact(transaction.vendeur), 44)

    canvas.text(left_x + 14.0, section_y - 42.0, buyer_name, font="F2", size=12.0, color=TEXT)
    canvas.text(left_x + 14.0, section_y - 62.0, buyer_contact, font="F1", size=10.5, color=TEXT)

    canvas.text(right_x + 14.0, section_y - 42.0, seller_name, font="F2", size=12.0, color=TEXT)
    canvas.text(right_x + 14.0, section_y - 62.0, seller_contact, font="F1", size=10.5, color=TEXT)

    # 3) Informations du véhicule (tableau)
    table_top = box_y - 28.0
    canvas.text(X, table_top, "INFORMATIONS DU VÉHICULE", font="F2", size=11.5, color=TEXT)
    canvas.save()
    canvas.set_stroke_color(*BORDER)
    canvas.set_line_width(1.0)
    canvas.line(X, table_top - 8.0, X + W, table_top - 8.0)
    canvas.restore()

    rows: list[tuple[str, str]] = [
        ("Identifiant annonce", f"#{voiture.id}"),
        ("Marque / Modèle", f"{(marque.nom if marque else '—')} {(modele.nom if modele else '—')}"),
        ("Année", str(getattr(voiture, "annee", "—"))),
        ("Kilométrage", f"{getattr(voiture, 'kilometrage', '—')} km"),
        ("État", str(getattr(voiture, "get_etat_display", lambda: '—')())),
    ]

    table_x = X
    table_y_top = table_top - 20.0
    label_w = 185.0
    header_h = 24.0
    row_h = 24.0
    table_h = header_h + row_h * len(rows)

    # Outer + header background
    canvas.save()
    canvas.set_fill_color(0.93, 0.95, 1.0)
    canvas.rect(table_x, table_y_top - header_h, W, header_h, stroke=False, fill=True)
    canvas.restore()

    canvas.save()
    canvas.set_stroke_color(*BORDER)
    canvas.set_line_width(1.0)
    canvas.rect(table_x, table_y_top - table_h, W, table_h, stroke=True, fill=False)
    canvas.line(table_x + label_w, table_y_top, table_x + label_w, table_y_top - table_h)
    canvas.line(table_x, table_y_top - header_h, table_x + W, table_y_top - header_h)
    canvas.restore()

    canvas.text(table_x + 12.0, table_y_top - 17.0, "Détail", font="F2", size=10.0, color=TEXT)
    canvas.text(table_x + label_w + 12.0, table_y_top - 17.0, "Valeur", font="F2", size=10.0, color=TEXT)

    y = table_y_top - header_h
    for idx, (label, value) in enumerate(rows):
        y_row_top = y - idx * row_h
        # Row separator
        canvas.save()
        canvas.set_stroke_color(*BORDER)
        canvas.set_line_width(1.0)
        canvas.line(table_x, y_row_top - row_h, table_x + W, y_row_top - row_h)
        canvas.restore()

        canvas.text(table_x + 12.0, y_row_top - 17.0, _truncate(label, 26), font="F1", size=10.0, color=MUTED)
        canvas.text(
            table_x + label_w + 12.0,
            y_row_top - 17.0,
            _truncate(value, 54),
            font="F2",
            size=10.5,
            color=TEXT,
        )

    # 4) Bloc financier
    fin_top = (table_y_top - table_h) - 26.0
    fin_h = 92.0
    canvas.save()
    canvas.set_fill_color(*LIGHT)
    canvas.set_stroke_color(*BORDER)
    canvas.set_line_width(1.0)
    canvas.rect(X, fin_top - fin_h, W, fin_h, stroke=True, fill=True)
    canvas.restore()

    canvas.text(X + 14.0, fin_top - 20.0, "BLOC FINANCIER", font="F2", size=10.0, color=MUTED)

    amount = _format_fcfa(transaction.prix_final)
    right_edge = X + W - 14.0

    canvas.text(X + 14.0, fin_top - 44.0, "Prix", font="F1", size=10.5, color=TEXT)
    _draw_text_right(canvas, x_right=right_edge, y=fin_top - 44.0, text=amount, font="F3", size=11.0, color=TEXT)

    canvas.save()
    canvas.set_stroke_color(*BORDER)
    canvas.set_line_width(1.0)
    canvas.line(X + 14.0, fin_top - 54.0, X + W - 14.0, fin_top - 54.0)
    canvas.restore()

    canvas.text(X + 14.0, fin_top - 78.0, "Total à payer", font="F2", size=12.0, color=TEXT)
    _draw_text_right(canvas, x_right=right_edge, y=fin_top - 80.0, text=amount, font="F2", size=14.0, color=TEXT)

    # 5) Pied de page
    footer = "Document généré automatiquement dans le cadre d’une simulation académique."
    _draw_text_center(
        canvas,
        x_center=X + (W / 2.0),
        y=M - 4.0,
        text=footer,
        font="F1",
        size=9.0,
        color=MUTED,
    )

    doc = build_one_page_pdf(
        content_stream=canvas.stream(),
        filename=filename,
        fonts={"F1": "Helvetica", "F2": "Helvetica-Bold", "F3": "Courier"},
    )
    return doc.content

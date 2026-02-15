from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django import template

register = template.Library()


def _to_decimal(value) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


@register.filter(name="fcfa")
def fcfa(value) -> str:
    """
    Format a numeric value as FCFA with thousands separated by spaces.
    Examples: 12500 -> "12 500 FCFA"
    """
    amount = _to_decimal(value)
    if amount is None:
        return "—"

    amount = amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    # Use space as thousands separator
    formatted = f"{int(amount):,}".replace(",", " ")
    return f"{formatted} FCFA"


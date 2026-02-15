from __future__ import annotations

from django.utils import timezone

from voitures.models import Transaction
from voitures.services.simple_pdf import build_simple_text_pdf


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


def build_transaction_receipt(*, transaction: Transaction, role: str) -> bytes:
    voiture = transaction.voiture
    modele = getattr(voiture, "modele", None)
    marque = getattr(modele, "marque", None)

    confirmation = transaction.date_confirmation or transaction.date_mise_a_jour or transaction.date_transaction
    if timezone.is_naive(confirmation):
        confirmation = timezone.make_aware(confirmation)

    title = "Reçu d'achat" if role == "buyer" else "Reçu de vente"
    filename = f"recu_transaction_{transaction.id}_{role}.pdf"

    lines = [
        f"Transaction: #{transaction.id}",
        f"Statut: {transaction.get_statut_display_fr()}",
        f"Date de confirmation: {confirmation.astimezone(timezone.get_current_timezone()).strftime('%d/%m/%Y %H:%M')}",
        "",
        "Véhicule",
        f"- ID annonce: #{voiture.id}",
        f"- Marque / Modèle: {(marque.nom if marque else '—')} {(modele.nom if modele else '—')}",
        f"- Année: {voiture.annee}",
        f"- État: {voiture.get_etat_display()}",
        f"- Couleur: {voiture.get_couleur_display()}",
        f"- Kilométrage: {voiture.kilometrage} km",
        "",
        f"Prix final: {transaction.prix_final} FCFA",
        "",
        f"Acheteur: {_user_label(transaction.acheteur)}",
        f"Vendeur: {_user_label(transaction.vendeur)}",
        "",
        "Signature acheteur: __________________________",
        "Signature vendeur: __________________________",
    ]

    doc = build_simple_text_pdf(title=title, lines=lines, filename=filename)
    return doc.content


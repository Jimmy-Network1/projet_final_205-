from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Avis, Conversation, Marque, Message, Modele, Transaction, Voiture


class TransactionFlowTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username="seller", password="Seller123!")
        self.buyer = User.objects.create_user(username="buyer", password="Buyer123!")
        self.marque = Marque.objects.create(
            nom="Renault", pays="France", date_creation="2000-01-01"
        )
        self.modele = Modele.objects.create(
            marque=self.marque,
            nom="Clio",
            annee_lancement=2010,
            type_carburant="essence",
            transmission="manuelle",
            puissance=90,
            consommation=5.2,
        )
        self.voiture = Voiture.objects.create(
            modele=self.modele,
            prix="10000.00",
            kilometrage=50000,
            annee=2020,
            couleur="gris",
            etat="occasion",
            description="Test",
            vendeur=self.seller,
            est_vendue=False,
            est_reservee=True,
        )
        self.trx = Transaction.objects.create(
            voiture=self.voiture,
            acheteur=self.buyer,
            vendeur=self.seller,
            prix_final=self.voiture.prix,
            statut="en_attente",
        )

    def test_buyer_can_cancel_pending_transaction(self):
        self.client.force_login(self.buyer)
        resp = self.client.post(reverse("annuler_transaction", args=[self.trx.id]))
        self.assertEqual(resp.status_code, 302)

        self.trx.refresh_from_db()
        self.voiture.refresh_from_db()
        self.assertEqual(self.trx.statut, "annulee")
        self.assertFalse(self.voiture.est_reservee)

    def test_seller_can_refuse_pending_transaction(self):
        self.client.force_login(self.seller)
        resp = self.client.post(reverse("refuser_transaction", args=[self.trx.id]))
        self.assertEqual(resp.status_code, 302)

        self.trx.refresh_from_db()
        self.voiture.refresh_from_db()
        self.assertEqual(self.trx.statut, "annulee")
        self.assertFalse(self.voiture.est_reservee)

    def test_logout_requires_post(self):
        self.client.force_login(self.buyer)
        resp = self.client.get(reverse("deconnexion"))
        self.assertEqual(resp.status_code, 405)

    def test_confirm_sale_sets_confirmation_date(self):
        self.client.force_login(self.seller)
        resp = self.client.post(reverse("confirmer_vente", args=[self.trx.id]))
        self.assertEqual(resp.status_code, 302)

        self.trx.refresh_from_db()
        self.assertEqual(self.trx.statut, "confirmee")
        self.assertIsNotNone(self.trx.date_confirmation)

    def test_receipt_pdf_download_for_buyer(self):
        self.client.force_login(self.seller)
        self.client.post(reverse("confirmer_vente", args=[self.trx.id]))
        self.trx.refresh_from_db()

        self.client.force_login(self.buyer)
        resp = self.client.get(reverse("telecharger_recu_transaction", args=[self.trx.id, "buyer"]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF"))


class AuthRedirectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u1", password="Pass123456!")

    def test_login_rejects_external_next(self):
        resp = self.client.post(
            reverse("connexion") + "?next=https://evil.example/",
            data={"username": "u1", "password": "Pass123456!", "next": "https://evil.example/"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp["Location"], reverse("accueil"))


class ListingModerationTests(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username="seller2", password="Seller123!")
        self.buyer = User.objects.create_user(username="buyer2", password="Buyer123!")
        self.marque = Marque.objects.create(
            nom="Peugeot", pays="France", date_creation="2000-01-01"
        )
        self.modele = Modele.objects.create(
            marque=self.marque,
            nom="208",
            annee_lancement=2015,
            type_carburant="essence",
            transmission="manuelle",
            puissance=100,
            consommation=5.5,
        )

    def test_pending_listing_hidden_from_public_list(self):
        Voiture.objects.create(
            modele=self.modele,
            prix="9000.00",
            kilometrage=60000,
            annee=2019,
            couleur="gris",
            etat="occasion",
            description="Pending",
            vendeur=self.seller,
            moderation_status="pending",
        )
        resp = self.client.get(reverse("liste_voitures"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["voitures"].paginator.count, 0)

    def test_pending_listing_detail_404_for_public(self):
        v = Voiture.objects.create(
            modele=self.modele,
            prix="9000.00",
            kilometrage=60000,
            annee=2019,
            couleur="gris",
            etat="occasion",
            description="Pending",
            vendeur=self.seller,
            moderation_status="pending",
        )
        resp = self.client.get(reverse("detail_voiture", args=[v.id]))
        self.assertEqual(resp.status_code, 404)

    def test_pending_listing_detail_visible_to_owner(self):
        v = Voiture.objects.create(
            modele=self.modele,
            prix="9000.00",
            kilometrage=60000,
            annee=2019,
            couleur="gris",
            etat="occasion",
            description="Pending",
            vendeur=self.seller,
            moderation_status="pending",
        )
        self.client.force_login(self.seller)
        resp = self.client.get(reverse("detail_voiture", args=[v.id]))
        self.assertEqual(resp.status_code, 200)

    def test_unapproved_listing_cannot_be_purchased(self):
        v = Voiture.objects.create(
            modele=self.modele,
            prix="9000.00",
            kilometrage=60000,
            annee=2019,
            couleur="gris",
            etat="occasion",
            description="Pending",
            vendeur=self.seller,
            moderation_status="pending",
        )
        self.client.force_login(self.buyer)
        resp = self.client.get(reverse("acheter_voiture", args=[v.id]))
        self.assertEqual(resp.status_code, 404)


class AdminModerationAndMessagingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin1", password="Admin123!", is_staff=True
        )
        self.seller = User.objects.create_user(username="seller3", password="Seller123!")
        self.buyer = User.objects.create_user(username="buyer3", password="Buyer123!")
        self.marque = Marque.objects.create(
            nom="Toyota", pays="Japon", date_creation="2000-01-01"
        )
        self.modele = Modele.objects.create(
            marque=self.marque,
            nom="Corolla",
            annee_lancement=2010,
            type_carburant="essence",
            transmission="manuelle",
            puissance=100,
            consommation=6.0,
        )

    def test_admin_reject_requires_reason(self):
        v = Voiture.objects.create(
            modele=self.modele,
            prix="12000.00",
            kilometrage=40000,
            annee=2020,
            couleur="gris",
            etat="occasion",
            description="Pending",
            vendeur=self.seller,
            moderation_status="pending",
        )
        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse("moderer_annonce", args=[v.id]),
            data={"action": "reject", "reason": ""},
        )
        self.assertEqual(resp.status_code, 302)
        v.refresh_from_db()
        self.assertEqual(v.moderation_status, "pending")

    def test_admin_can_reject_listing_with_reason(self):
        v = Voiture.objects.create(
            modele=self.modele,
            prix="12000.00",
            kilometrage=40000,
            annee=2020,
            couleur="gris",
            etat="occasion",
            description="Pending",
            vendeur=self.seller,
            moderation_status="pending",
        )
        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse("moderer_annonce", args=[v.id]),
            data={"action": "reject", "reason": "Photos floues"},
        )
        self.assertEqual(resp.status_code, 302)
        v.refresh_from_db()
        self.assertEqual(v.moderation_status, "rejected")
        self.assertEqual(v.moderation_reason, "Photos floues")
        self.assertEqual(v.moderated_by_id, self.admin.id)

    def test_listing_message_creates_conversation(self):
        v = Voiture.objects.create(
            modele=self.modele,
            prix="12000.00",
            kilometrage=40000,
            annee=2020,
            couleur="gris",
            etat="occasion",
            description="Approved",
            vendeur=self.seller,
            moderation_status="approved",
        )
        self.client.force_login(self.buyer)
        resp = self.client.post(
            reverse("envoyer_message", args=[v.id]),
            data={"contenu": "Bonjour, la voiture est-elle disponible ?"},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Conversation.objects.exists())
        self.assertTrue(Message.objects.exists())

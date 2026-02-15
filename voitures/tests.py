from __future__ import annotations

import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
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


class BrandUiTests(TestCase):
    def test_marque_logo_svg_endpoint(self):
        marque = Marque.objects.create(nom="Citroën", pays="France", date_creation="2000-01-01")
        resp = self.client.get(reverse("marque_logo_svg", args=[marque.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp["Content-Type"].startswith("image/svg+xml"))
        self.assertIn(b"CI", resp.content.upper())

    def test_marque_logo_endpoint_catalog_then_fallback(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            catalog = Path(tmpdir)
            catalog.joinpath("citroen.svg").write_text("<svg>CI</svg>", encoding="utf-8")

            with override_settings(BRAND_LOGO_CATALOG_DIR=catalog):
                marque = Marque.objects.create(nom="Citroën", pays="France", date_creation="2000-01-01")
                resp = self.client.get(reverse("marque_logo", args=[marque.id]))
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp["Content-Type"].startswith("image/svg+xml"))
                body = b"".join(resp.streaming_content)
                self.assertIn(b"CI", body.upper())

                other = Marque.objects.create(nom="NoBrand", pays="—", date_creation="2000-01-01")
                resp2 = self.client.get(reverse("marque_logo", args=[other.id]))
                self.assertEqual(resp2.status_code, 200)
                self.assertTrue(resp2["Content-Type"].startswith("image/svg+xml"))

    def test_admin_can_access_marque_crud_pages(self):
        admin_user = User.objects.create_superuser(
            username="admin",
            password="Admin123!",
            email="admin@test.local",
        )
        self.client.force_login(admin_user)
        self.assertEqual(self.client.get(reverse("admin:voitures_marque_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:voitures_marque_add")).status_code, 200)

    def test_dashboard_marques_requires_staff(self):
        user = User.objects.create_user(username="u1", password="Pass123456!")
        self.client.force_login(user)
        resp = self.client.get(reverse("dashboard_marques"))
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_marques_allows_add_with_logo(self):
        admin_user = User.objects.create_user(username="admin2", password="Admin123!", is_staff=True)
        self.client.force_login(admin_user)

        png = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        logo = SimpleUploadedFile("brand.png", png, content_type="image/png")

        with tempfile.TemporaryDirectory() as media_tmp:
            with override_settings(MEDIA_ROOT=media_tmp):
                resp = self.client.post(
                    reverse("dashboard_marque_add"),
                    data={
                        "nom": "Tesla",
                        "pays": "USA",
                        "date_creation": "2000-01-01",
                        "description": "Electric",
                        "logo": logo,
                    },
                    follow=True,
                )
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(Marque.objects.filter(nom="Tesla").exists())
                marque = Marque.objects.get(nom="Tesla")
                self.assertTrue(getattr(marque.logo, "name", ""))

    def test_new_marque_appears_in_publish_form(self):
        marque = Marque.objects.create(nom="Tesla", pays="USA", date_creation="2000-01-01")
        user = User.objects.create_user(username="u1", password="Pass123456!")
        self.client.force_login(user)
        resp = self.client.get(reverse("ajouter_voiture"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, marque.nom)

    def test_public_brands_page_lists_all_marques(self):
        m1 = Marque.objects.create(nom="Renault", pays="France", date_creation="2000-01-01")
        m2 = Marque.objects.create(nom="Toyota", pays="Japon", date_creation="2000-01-01")
        resp = self.client.get(reverse("liste_marques"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, m1.nom)
        self.assertContains(resp, m2.nom)

from __future__ import annotations

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Marque, Modele, Transaction, Voiture


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

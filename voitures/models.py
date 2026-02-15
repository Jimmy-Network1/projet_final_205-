from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import os
from datetime import datetime

class Marque(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    pays = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    date_creation = models.DateField()
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['nom']
        verbose_name = 'Marque'
        verbose_name_plural = 'Marques'
    
    def __str__(self):
        return self.nom
    
    def nombre_modeles(self):
        return self.modeles.count()
    
    def nombre_voitures(self):
        return Voiture.objects.filter(modele__marque=self).count()

class Modele(models.Model):
    TYPE_CARBURANT = [
        ('essence', 'Essence'),
        ('diesel', 'Diesel'),
        ('hybride', 'Hybride'),
        ('electrique', 'Électrique'),
        ('gpl', 'GPL'),
    ]
    
    TRANSMISSION = [
        ('manuelle', 'Manuelle'),
        ('automatique', 'Automatique'),
        ('semi-auto', 'Semi-automatique'),
    ]
    
    marque = models.ForeignKey(Marque, on_delete=models.CASCADE, related_name='modeles')
    nom = models.CharField(max_length=100)
    annee_lancement = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2026)]
    )
    type_carburant = models.CharField(max_length=20, choices=TYPE_CARBURANT, default='essence')
    transmission = models.CharField(max_length=20, choices=TRANSMISSION, default='manuelle')
    puissance = models.PositiveIntegerField(help_text="Puissance en chevaux", default=100)
    consommation = models.FloatField(help_text="Consommation en L/100km", default=6.0)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['marque', 'nom']
        unique_together = ['marque', 'nom']
        verbose_name = 'Modèle'
        verbose_name_plural = 'Modèles'
    
    def __str__(self):
        return f"{self.marque.nom} {self.nom}"
    
    def nombre_voitures(self):
        return self.voitures.count()

class Voiture(models.Model):
    ETAT_CHOICES = [
        ('neuf', 'Neuf'),
        ('occasion', 'Occasion'),
        ('reconditionne', 'Reconditionné'),
    ]
    
    COULEUR_CHOICES = [
        ('blanc', 'Blanc'),
        ('noir', 'Noir'),
        ('gris', 'Gris'),
        ('rouge', 'Rouge'),
        ('bleu', 'Bleu'),
        ('vert', 'Vert'),
        ('jaune', 'Jaune'),
        ('argent', 'Argent'),
        ('orange', 'Orange'),
        ('violet', 'Violet'),
        ('marron', 'Marron'),
        ('beige', 'Beige'),
    ]
    
    modele = models.ForeignKey(Modele, on_delete=models.CASCADE, related_name='voitures')
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    kilometrage = models.PositiveIntegerField(default=0)
    annee = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2026)]
    )
    couleur = models.CharField(max_length=20, choices=COULEUR_CHOICES)
    etat = models.CharField(max_length=20, choices=ETAT_CHOICES)
    description = models.TextField()
    date_ajout = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='voitures_vendues')
    est_vendue = models.BooleanField(default=False)
    est_reservee = models.BooleanField(default=False)
    est_louee = models.BooleanField(default=False)
    localisation = models.CharField(max_length=120, default="Dépôt")
    carburant_niveau = models.PositiveSmallIntegerField(default=100)
    gps_tracking_url = models.URLField(blank=True, default="")
    image_principale = models.ImageField(
        upload_to='voitures/', 
        default='voitures/default.jpg',
        blank=True
    )
    vue = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-date_ajout']
        verbose_name = 'Voiture'
        verbose_name_plural = 'Voitures'
    
    def __str__(self):
        return f"{self.modele} - {self.annee} - {self.couleur}"
    
    def incrementer_vue(self):
        self.vue += 1
        self.save(update_fields=['vue'])
    
    def prix_format(self):
        if self.prix is None:
            return "Prix non défini"
        try:
            return f"{float(self.prix):,.0f} FCFA".replace(",", " ")
        except (TypeError, ValueError):
            return "Prix invalide"
    
    def age(self):
        if self.annee is None:
            return "Année non définie"
        try:
            return timezone.now().year - self.annee
        except (TypeError, ValueError):
            return "Année invalide"
    
    def est_recente(self):
        if self.annee is None:
            return False
        try:
            return (timezone.now().year - self.annee) <= 2
        except (TypeError, ValueError):
            return False
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('detail_voiture', args=[str(self.id)])

class ImageVoiture(models.Model):
    voiture = models.ForeignKey(Voiture, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='voitures/details/')
    description = models.CharField(max_length=200, blank=True)
    ordre = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['ordre']
        verbose_name = 'Image de voiture'
        verbose_name_plural = 'Images de voitures'
    
    def __str__(self):
        return f"Image de {self.voiture}"

class Favori(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favoris')
    voiture = models.ForeignKey(Voiture, on_delete=models.CASCADE, related_name='favoris')
    date_ajout = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['utilisateur', 'voiture']
        ordering = ['-date_ajout']
        verbose_name = 'Favori'
        verbose_name_plural = 'Favoris'
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.voiture}"

class Avis(models.Model):
    voiture = models.ForeignKey(Voiture, on_delete=models.CASCADE, related_name='avis')
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    commentaire = models.TextField()
    date_publication = models.DateTimeField(auto_now_add=True)
    approuve = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_publication']
        unique_together = ['voiture', 'utilisateur']
        verbose_name = 'Avis'
        verbose_name_plural = 'Avis'
    
    def __str__(self):
        return f"Avis de {self.utilisateur.username} sur {self.voiture}"

class Transaction(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirmee', 'Confirmée'),
        ('annulee', 'Annulée'),
        ('terminee', 'Terminée'),
    ]
    
    voiture = models.ForeignKey(Voiture, on_delete=models.CASCADE)
    acheteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achats')
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ventes')
    prix_final = models.DecimalField(max_digits=10, decimal_places=2)
    date_transaction = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-date_transaction']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
    
    def __str__(self):
        return f"Transaction #{self.id} - {self.voiture}"
    
    def est_terminee(self):
        return self.statut == 'terminee'
    
    def est_annulee(self):
        return self.statut == 'annulee'
    
    def est_en_attente(self):
        return self.statut == 'en_attente'
    
    def get_statut_display_fr(self):
        statuts = {
            'en_attente': 'En attente',
            'confirmee': 'Confirmée',
            'annulee': 'Annulée',
            'terminee': 'Terminée',
        }
        return statuts.get(self.statut, self.statut)


class Reservation(models.Model):
    STATUTS = [
        ("en_attente", "En attente"),
        ("acceptee", "Acceptée"),
        ("refusee", "Refusée"),
        ("annulee", "Annulée"),
        ("terminee", "Terminée"),
    ]

    TYPE_CHOICES = [
        ("reservation", "Réservation véhicule"),
        ("essai", "Essai"),
    ]

    voiture = models.ForeignKey(Voiture, on_delete=models.CASCADE, related_name="reservations")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reservations")
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="reservation")
    debut = models.DateTimeField()
    fin = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=STATUTS, default="en_attente")
    note = models.TextField(blank=True)
    signature = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"

    def __str__(self):
        return f"Reservation #{self.id} - {self.voiture}"

    @property
    def is_active(self):
        return self.statut in {"en_attente", "acceptee"} and self.fin > timezone.now()

    @staticmethod
    def overlaps(voiture_id: int, start: datetime, end: datetime) -> bool:
        return Reservation.objects.filter(
            voiture_id=voiture_id,
            statut__in=["en_attente", "acceptee"],
            debut__lt=end,
            fin__gt=start,
        ).exists()


class Location(models.Model):
    STATUTS = [
        ("a_venir", "À venir"),
        ("en_cours", "En cours"),
        ("terminee", "Terminée"),
        ("annulee", "Annulée"),
    ]

    voiture = models.ForeignKey(Voiture, on_delete=models.CASCADE, related_name="locations")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="locations")
    debut = models.DateTimeField()
    fin = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=STATUTS, default="a_venir")
    kilometrage_depart = models.PositiveIntegerField(null=True, blank=True)
    carburant_depart = models.PositiveSmallIntegerField(null=True, blank=True)
    kilometrage_retour = models.PositiveIntegerField(null=True, blank=True)
    carburant_retour = models.PositiveSmallIntegerField(null=True, blank=True)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    conditions = models.TextField(blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Location"
        verbose_name_plural = "Locations"
        indexes = [
            models.Index(fields=["voiture", "statut", "debut", "fin"]),
        ]

    def __str__(self):
        return f"Location #{self.id} - {self.voiture}"

    @staticmethod
    def overlaps(voiture_id: int, start: datetime, end: datetime) -> bool:
        return Location.objects.filter(
            voiture_id=voiture_id,
            statut__in=["a_venir", "en_cours"],
            debut__lt=end,
            fin__gt=start,
        ).exists()

class Message(models.Model):
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_recus')
    sujet = models.CharField(max_length=200)
    contenu = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_envoi']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
    
    def __str__(self):
        return f"{self.expediteur} -> {self.destinataire}: {self.sujet}"
    
    def marquer_comme_lu(self):
        self.lu = True
        self.save()


class Notification(models.Model):
    TYPE_CHOICES = [
        ("new_listing", "Nouvelle annonce"),
        ("purchase_request", "Demande d'achat"),
        ("sale_confirmed", "Vente confirmée"),
        ("message", "Message"),
    ]

    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=200)
    contenu = models.TextField(blank=True)
    url = models.CharField(max_length=300, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.utilisateur.username}: {self.titre}"

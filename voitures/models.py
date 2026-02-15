from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import os

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

    MODERATION_STATUS_CHOICES = [
        ("pending", "En attente"),
        ("approved", "Approuvée"),
        ("rejected", "Refusée"),
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
    moderation_status = models.CharField(
        max_length=12,
        choices=MODERATION_STATUS_CHOICES,
        default="pending",
        db_index=True,
    )
    moderation_reason = models.TextField(blank=True)
    moderated_at = models.DateTimeField(blank=True, null=True)
    moderated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="voitures_moderees",
    )
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

    def est_approuvee(self) -> bool:
        return self.moderation_status == "approved"
    
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
    date_confirmation = models.DateTimeField(blank=True, null=True)
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

class Message(models.Model):
    conversation = models.ForeignKey(
        "Conversation",
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True,
    )
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_envoyes')
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_recus')
    voiture = models.ForeignKey(Voiture, on_delete=models.SET_NULL, null=True, blank=True)
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


class Conversation(models.Model):
    """
    Conversation 1:1 entre deux utilisateurs, optionnellement liée à une annonce.
    `is_support=True` pour les échanges avec l'admin/support.
    """

    participant_a = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations_a")
    participant_b = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations_b")
    voiture = models.ForeignKey(Voiture, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
    is_support = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["participant_a", "participant_b", "voiture", "is_support"],
                name="uniq_conversation_participants_voiture_support",
            )
        ]

    def __str__(self):
        return f"{self.participant_a.username} ↔ {self.participant_b.username}"

    def other_for(self, user: User) -> User | None:
        if user_id := getattr(user, "id", None):
            if self.participant_a_id == user_id:
                return self.participant_b
            if self.participant_b_id == user_id:
                return self.participant_a
        return None

class Notification(models.Model):
    TYPE_CHOICES = [
        ("new_listing", "Nouvelle annonce"),
        ("listing_moderation", "Validation annonce"),
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

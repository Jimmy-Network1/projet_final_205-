from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Marque, Modele, Voiture, ImageVoiture, 
    Favori, Avis, Transaction, Message, Notification
)

class ImageVoitureInline(admin.TabularInline):
    model = ImageVoiture
    extra = 1
    fields = ['image', 'description', 'ordre']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 100px;" />', obj.image.url)
        return "-"
    image_preview.short_description = "Aperçu"

@admin.register(Marque)
class MarqueAdmin(admin.ModelAdmin):
    list_display = ['nom', 'pays', 'date_creation', 'nombre_modeles', 'nombre_voitures']
    list_filter = ['pays', 'date_creation']
    search_fields = ['nom', 'pays']
    readonly_fields = ['nombre_modeles', 'nombre_voitures']
    fieldsets = (
        ('Informations', {
            'fields': ('nom', 'pays', 'date_creation', 'logo', 'description')
        }),
        ('Statistiques', {
            'fields': ('nombre_modeles', 'nombre_voitures'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Modele)
class ModeleAdmin(admin.ModelAdmin):
    list_display = ['marque', 'nom', 'annee_lancement', 'type_carburant', 'transmission', 'nombre_voitures']
    list_filter = ['marque', 'type_carburant', 'transmission']
    search_fields = ['nom', 'marque__nom']
    readonly_fields = ['nombre_voitures']

@admin.register(Voiture)
class VoitureAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "modele",
        "annee",
        "get_prix_format",
        "vendeur",
        "moderation_status",
        "est_vendue",
        "date_ajout",
    ]
    list_filter = ["moderation_status", "est_vendue", "etat", "couleur", "modele__marque", "date_ajout"]
    search_fields = ['modele__nom', 'modele__marque__nom', 'vendeur__username', 'description']
    readonly_fields = [
        "date_ajout",
        "date_modification",
        "vue",
        "get_prix_format",
        "get_age",
        "get_est_recente",
        "moderated_at",
    ]
    inlines = [ImageVoitureInline]
    list_per_page = 20
    actions = ["approve_listings", "reject_listings"]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('modele', 'vendeur', 'prix', 'get_prix_format')
        }),
        ('Caractéristiques', {
            'fields': ('annee', 'kilometrage', 'couleur', 'etat', 'description')
        }),
        ('Images', {
            'fields': ('image_principale',)
        }),
        ('Statut', {
            'fields': ('moderation_status', 'moderated_at', 'est_vendue',)
        }),
        ('Statistiques', {
            'fields': ('vue', 'date_ajout', 'date_modification', 'get_age', 'get_est_recente'),
            'classes': ('collapse',)
        }),
    )
    
    def get_prix_format(self, obj):
        # Vérifie si l'objet a un ID (existe dans la base de données)
        if obj.pk and obj.prix is not None:
            return obj.prix_format()
        return "Prix non défini"
    get_prix_format.short_description = 'Prix formaté'
    
    def get_age(self, obj):
        # Vérifie si l'objet a un ID et si l'année est définie
        if obj.pk and obj.annee is not None:
            age_value = obj.age()
            if isinstance(age_value, int):
                return f"{age_value} ans"
            return age_value
        return "Année non définie"
    get_age.short_description = 'Âge'
    
    def get_est_recente(self, obj):
        # Vérifie si l'objet a un ID et si l'année est définie
        if obj.pk and obj.annee is not None:
            return "Oui" if obj.est_recente() else "Non"
        return "N/A"
    get_est_recente.short_description = 'Récente'

    @admin.action(description="Approuver les annonces sélectionnées")
    def approve_listings(self, request, queryset):
        now = timezone.now()
        to_approve = list(
            queryset.select_related("vendeur", "modele__marque", "modele").exclude(moderation_status="approved")
        )
        updated = Voiture.objects.filter(id__in=[v.id for v in to_approve]).update(
            moderation_status="approved",
            moderated_at=now,
        )

        notifications = []
        for v in to_approve:
            if v.vendeur and v.vendeur.is_active:
                notifications.append(
                    Notification(
                        utilisateur=v.vendeur,
                        type="listing_moderation",
                        titre="Annonce approuvée",
                        contenu=f"Votre annonce #{v.id} est maintenant visible.",
                        url=v.get_absolute_url(),
                    )
                )
        if notifications:
            Notification.objects.bulk_create(notifications)

        self.message_user(request, f"{updated} annonce(s) approuvée(s).")

    @admin.action(description="Refuser les annonces sélectionnées")
    def reject_listings(self, request, queryset):
        now = timezone.now()
        to_reject = list(
            queryset.select_related("vendeur").exclude(moderation_status="rejected")
        )
        updated = Voiture.objects.filter(id__in=[v.id for v in to_reject]).update(
            moderation_status="rejected",
            moderated_at=now,
        )

        notifications = []
        for v in to_reject:
            if v.vendeur and v.vendeur.is_active:
                notifications.append(
                    Notification(
                        utilisateur=v.vendeur,
                        type="listing_moderation",
                        titre="Annonce refusée",
                        contenu=f"Votre annonce #{v.id} a été refusée. Modifiez-la puis renvoyez-la.",
                        url=v.get_absolute_url(),
                    )
                )
        if notifications:
            Notification.objects.bulk_create(notifications)

        self.message_user(request, f"{updated} annonce(s) refusée(s).")

@admin.register(Favori)
class FavoriAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'voiture', 'date_ajout']
    list_filter = ['date_ajout']
    search_fields = ['utilisateur__username', 'voiture__modele__nom']
    readonly_fields = ['date_ajout']

@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display = ['voiture', 'utilisateur', 'note', 'approuve', 'date_publication']
    list_filter = ['approuve', 'note', 'date_publication']
    search_fields = ['voiture__modele__nom', 'utilisateur__username', 'commentaire']
    readonly_fields = ['date_publication']
    actions = ['approuver_avis', 'desapprouver_avis']
    
    def approuver_avis(self, request, queryset):
        queryset.update(approuve=True)
        self.message_user(request, f"{queryset.count()} avis ont été approuvés.")
    approuver_avis.short_description = "Approuver les avis sélectionnés"
    
    def desapprouver_avis(self, request, queryset):
        queryset.update(approuve=False)
        self.message_user(request, f"{queryset.count()} avis ont été désapprouvés.")
    desapprouver_avis.short_description = "Désapprouver les avis sélectionnés"

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'voiture', 'acheteur', 'vendeur', 'prix_final', 'statut', 'date_transaction']
    list_filter = ['statut', 'date_transaction']
    search_fields = ['voiture__modele__nom', 'acheteur__username', 'vendeur__username']
    readonly_fields = ['date_transaction', 'date_mise_a_jour']
    list_per_page = 20
    
    fieldsets = (
        ('Transaction', {
            'fields': ('voiture', 'acheteur', 'vendeur', 'prix_final', 'statut')
        }),
        ('Dates', {
            'fields': ('date_transaction', 'date_mise_a_jour'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['expediteur', 'destinataire', 'sujet', 'date_envoi', 'lu']
    list_filter = ['lu', 'date_envoi']
    search_fields = ['expediteur__username', 'destinataire__username', 'sujet', 'contenu']
    readonly_fields = ['date_envoi']
    actions = ['marquer_comme_lu', 'marquer_comme_non_lu']
    
    def marquer_comme_lu(self, request, queryset):
        queryset.update(lu=True)
        self.message_user(request, f"{queryset.count()} messages marqués comme lus.")
    marquer_comme_lu.short_description = "Marquer comme lu"
    
    def marquer_comme_non_lu(self, request, queryset):
        queryset.update(lu=False)
        self.message_user(request, f"{queryset.count()} messages marqués comme non lus.")
    marquer_comme_non_lu.short_description = "Marquer comme non lu"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["utilisateur", "type", "titre", "lu", "date_creation"]
    list_filter = ["type", "lu", "date_creation"]
    search_fields = ["utilisateur__username", "titre", "contenu"]
    readonly_fields = ["date_creation"]

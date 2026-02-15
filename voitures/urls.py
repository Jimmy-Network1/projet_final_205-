from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import PasswordResetEmailForm, SetPasswordStyledForm

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('voitures/', views.liste_voitures, name='liste_voitures'),
    path('voiture/<int:voiture_id>/', views.detail_voiture, name='detail_voiture'),
    path('voiture/ajouter/', views.ajouter_voiture, name='ajouter_voiture'),
    path('voiture/<int:voiture_id>/modifier/', views.modifier_voiture, name='modifier_voiture'),
    path('voiture/<int:voiture_id>/supprimer/', views.supprimer_voiture, name='supprimer_voiture'),  # AJOUTÉ
    path('voiture/<int:voiture_id>/favori/', views.toggle_favori, name='toggle_favori'),
    path('voiture/<int:voiture_id>/acheter/', views.acheter_voiture, name='acheter_voiture'),
    path('voiture/<int:voiture_id>/reserver/', views.reserver_voiture, name='reserver_voiture'),
    path('voiture/<int:voiture_id>/avis/', views.ajouter_avis, name='ajouter_avis'),
    path('voiture/<int:voiture_id>/message/', views.envoyer_message, name='envoyer_message'),
    
    path('mes-voitures/', views.mes_voitures, name='mes_voitures'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
    path('mes-achats/', views.mes_achats, name='mes_achats'),
    path('mes-ventes/', views.mes_ventes, name='mes_ventes'),
    path('mes-messages/', views.mes_messages, name='mes_messages'),
    path('notifications/', views.notifications, name='notifications'),
    path('transaction/<int:transaction_id>/confirmer/', views.confirmer_vente, name='confirmer_vente'),
    path('transaction/<int:transaction_id>/annuler/', views.annuler_transaction, name='annuler_transaction'),
    path('transaction/<int:transaction_id>/refuser/', views.refuser_transaction, name='refuser_transaction'),
    
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),
    path('deconnexion/', views.deconnexion, name='deconnexion'),

    path(
        'mot-de-passe/oubli/',
        auth_views.PasswordResetView.as_view(form_class=PasswordResetEmailForm),
        name='password_reset',
    ),
    path('mot-de-passe/oubli/envoye/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path(
        'mot-de-passe/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(form_class=SetPasswordStyledForm),
        name='password_reset_confirm',
    ),
    path('mot-de-passe/reset/termine/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Pages d'administration (pour les utilisateurs staff)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Page de test
    path('test/', views.test, name='test'),
]

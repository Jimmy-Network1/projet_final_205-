from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from . import views_branding
from .forms import PasswordResetEmailForm, SetPasswordStyledForm

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path("marques/<int:marque_id>/logo/", views_branding.marque_logo, name="marque_logo"),
    path("marques/<int:marque_id>/logo.svg", views_branding.marque_logo_svg, name="marque_logo_svg"),
    path("marques/", views.liste_marques, name="liste_marques"),
    path('voitures/', views.liste_voitures, name='liste_voitures'),
    path('voiture/<int:voiture_id>/', views.detail_voiture, name='detail_voiture'),
    path('voiture/ajouter/', views.ajouter_voiture, name='ajouter_voiture'),
    path('voiture/<int:voiture_id>/modifier/', views.modifier_voiture, name='modifier_voiture'),
    path('voiture/<int:voiture_id>/supprimer/', views.supprimer_voiture, name='supprimer_voiture'),  # AJOUTÉ
    path('voiture/<int:voiture_id>/favori/', views.toggle_favori, name='toggle_favori'),
    path('voiture/<int:voiture_id>/acheter/', views.acheter_voiture, name='acheter_voiture'),
    path('voiture/<int:voiture_id>/avis/', views.ajouter_avis, name='ajouter_avis'),
    path('voiture/<int:voiture_id>/message/', views.envoyer_message, name='envoyer_message'),
    
    path('mes-voitures/', views.mes_voitures, name='mes_voitures'),
    path('mes-favoris/', views.mes_favoris, name='mes_favoris'),
    path('mes-achats/', views.mes_achats, name='mes_achats'),
    path('mes-ventes/', views.mes_ventes, name='mes_ventes'),
    path('mes-messages/', views.mes_messages, name='mes_messages'),
    path('messages/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('notifications/', views.notifications, name='notifications'),
    path('transaction/<int:transaction_id>/confirmer/', views.confirmer_vente, name='confirmer_vente'),
    path('transaction/<int:transaction_id>/annuler/', views.annuler_transaction, name='annuler_transaction'),
    path('transaction/<int:transaction_id>/refuser/', views.refuser_transaction, name='refuser_transaction'),
    path(
        "transaction/<int:transaction_id>/recu/<str:role>/",
        views.telecharger_recu_transaction,
        name="telecharger_recu_transaction",
    ),
    
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
    path("dashboard/marques/", views.dashboard_marques, name="dashboard_marques"),
    path("dashboard/marques/ajouter/", views.dashboard_marque_add, name="dashboard_marque_add"),
    path("dashboard/marques/<int:marque_id>/modifier/", views.dashboard_marque_edit, name="dashboard_marque_edit"),
    path("dashboard/marques/<int:marque_id>/supprimer/", views.dashboard_marque_delete, name="dashboard_marque_delete"),
    path('dashboard/annonce/<int:voiture_id>/moderation/', views.moderer_annonce, name='moderer_annonce'),
    path('dashboard/avis/<int:avis_id>/moderation/', views.moderer_avis, name='moderer_avis'),
    path("support/", views.support_inbox, name="support_inbox"),
    path("support/start/<int:user_id>/", views.support_start, name="support_start"),
    
    # Page de test
    path('test/', views.test, name='test'),
]

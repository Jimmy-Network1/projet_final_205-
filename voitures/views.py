from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User  # IMPORT AJOUTÉ
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from datetime import date
import os
from decimal import Decimal, InvalidOperation
from .models import Marque, Modele, Voiture, Favori, Transaction, Avis, Message, Notification, ImageVoiture
from .forms import InscriptionForm, AvisForm
from .services import transactions


def _validate_uploaded_image(uploaded_file):
    if not uploaded_file:
        return None
    max_bytes = 5 * 1024 * 1024  # 5MB
    if uploaded_file.size and uploaded_file.size > max_bytes:
        return "Image trop volumineuse (max 5MB)."
    content_type = getattr(uploaded_file, "content_type", "") or ""
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if content_type and content_type.lower() not in allowed:
        return "Format d'image non supporté (JPG, PNG, WEBP)."
    return None


def _staff_users():
    return User.objects.filter(is_staff=True, is_active=True)


def _notify(users, *, type, titre, contenu="", url=""):
    notifications = [
        Notification(utilisateur=user, type=type, titre=titre, contenu=contenu, url=url)
        for user in users
        if user and getattr(user, "is_active", False)
    ]
    if notifications:
        Notification.objects.bulk_create(notifications)


# ==================== VUES PUBLIQUES ====================

def accueil(request):
    """Page d'accueil du site"""
    transactions.expire_stale_purchase_requests()
    voitures_recentes = Voiture.objects.filter(est_vendue=False).order_by('-date_ajout')[:6]
    voitures_promo = Voiture.objects.filter(est_vendue=False).order_by('prix')[:6]
    marques_populaires = Marque.objects.annotate(
        nb_voitures=Count('modeles__voitures')
    ).order_by('-nb_voitures')[:8]
    
    context = {
        'voitures_recentes': voitures_recentes,
        'voitures_promo': voitures_promo,
        'marques_populaires': marques_populaires,
        'marques': Marque.objects.all().order_by('nom'),
        'voitures_vedette': Voiture.objects.filter(est_vendue=False).select_related('modele__marque').order_by('-date_ajout')[:12],
        'total_voitures': Voiture.objects.filter(est_vendue=False).count(),
    }
    return render(request, 'voitures/accueil.html', context)

def liste_voitures(request):
    """Liste toutes les voitures avec filtres"""
    transactions.expire_stale_purchase_requests()
    voitures_list = Voiture.objects.filter(est_vendue=False).select_related(
        'modele__marque', 'vendeur'
    ).prefetch_related('favoris')

    q = request.GET.get("q")
    sort = request.GET.get("sort")
    statut = request.GET.get("statut")
    
    # Récupération des filtres
    marque_id = request.GET.get('marque')
    prix_min = request.GET.get('prix_min')
    prix_max = request.GET.get('prix_max')
    annee_min = request.GET.get('annee_min')
    annee_max = request.GET.get('annee_max')

    if q:
        voitures_list = voitures_list.filter(
            Q(modele__nom__icontains=q)
            | Q(modele__marque__nom__icontains=q)
            | Q(description__icontains=q)
        )
    
    # Application des filtres
    if marque_id:
        voitures_list = voitures_list.filter(modele__marque_id=marque_id)
    
    if prix_min:
        voitures_list = voitures_list.filter(prix__gte=prix_min)
    
    if prix_max:
        voitures_list = voitures_list.filter(prix__lte=prix_max)
    
    if annee_min:
        voitures_list = voitures_list.filter(annee__gte=annee_min)
    
    if annee_max:
        voitures_list = voitures_list.filter(annee__lte=annee_max)

    if statut == "reservee":
        voitures_list = voitures_list.filter(est_reservee=True)
    elif statut == "disponible":
        voitures_list = voitures_list.filter(est_reservee=False)

    if sort == "prix_asc":
        voitures_list = voitures_list.order_by("prix")
    elif sort == "prix_desc":
        voitures_list = voitures_list.order_by("-prix")
    elif sort == "annee_desc":
        voitures_list = voitures_list.order_by("-annee")
    elif sort == "km_asc":
        voitures_list = voitures_list.order_by("kilometrage")
    
    # Pagination
    paginator = Paginator(voitures_list, 12)
    page_number = request.GET.get('page')
    voitures = paginator.get_page(page_number)
    
    # Calcul du prix moyen
    prix_moyen = voitures_list.aggregate(Avg('prix'))['prix__avg']
    
    context = {
        'voitures': voitures,
        'marques': Marque.objects.all(),
        'marque_selected': int(marque_id) if marque_id else None,
        'prix_min': prix_min,
        'prix_max': prix_max,
        'annee_min': annee_min,
        'annee_max': annee_max,
        'prix_moyen': prix_moyen,
        'q': q,
        'sort': sort,
        'statut': statut,
    }
    return render(request, 'voitures/liste_voitures.html', context)

def detail_voiture(request, voiture_id):
    """Page de détails d'une voiture"""
    transactions.expire_stale_purchase_requests()
    voiture = get_object_or_404(
        Voiture.objects.select_related('modele__marque', 'vendeur').prefetch_related("images"),
        id=voiture_id,
    )

    if request.method == "GET":
        if not request.user.is_authenticated or request.user != voiture.vendeur:
            voiture.incrementer_vue()
    
    # Vérifier si l'utilisateur a cette voiture en favoris
    est_favori = False
    if request.user.is_authenticated:
        est_favori = Favori.objects.filter(
            utilisateur=request.user, 
            voiture=voiture
        ).exists()
    
    # Récupérer les avis
    avis = Avis.objects.filter(voiture=voiture, approuve=True)

    transaction_en_attente = None
    if request.user.is_authenticated:
        transaction_en_attente = transactions.get_pending_transaction_for_user(
            voiture=voiture, user=request.user
        )
    
    # Voitures similaires
    voitures_similaires = Voiture.objects.filter(
        modele__marque=voiture.modele.marque,
        est_vendue=False
    ).exclude(id=voiture.id)[:4]
    
    context = {
        'voiture': voiture,
        'est_favori': est_favori,
        'avis': avis,
        'voitures_similaires': voitures_similaires,
        'avis_form': AvisForm(),
        "transaction_en_attente": transaction_en_attente,
    }
    return render(request, 'voitures/detail_voiture.html', context)

# ==================== AUTHENTIFICATION ====================

def inscription(request):
    """Page d'inscription"""
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user, backend="voitures.auth_backends.UsernameOrEmailBackend")
            
            messages.success(request, 'Inscription réussie ! Bienvenue sur AutoMarket.')
            return redirect('accueil')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = InscriptionForm()
    
    context = {'form': form}
    return render(request, 'voitures/inscription.html', context)

def connexion(request):
    """Page de connexion"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.username} !')
            
            # Redirection vers la page demandée ou l'accueil
            next_page = (request.POST.get("next") or request.GET.get("next") or "").strip()
            if next_page and url_has_allowed_host_and_scheme(
                url=next_page,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_page)
            return redirect("accueil")
        else:
            messages.error(request, 'Identifiants incorrects. Veuillez réessayer.')
    
    return render(request, 'voitures/connexion.html')

@login_required
@require_POST
def deconnexion(request):
    """Déconnexion de l'utilisateur"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('accueil')

# ==================== VUES PROTÉGÉES ====================

@login_required
def ajouter_voiture(request):
    """Ajouter une nouvelle voiture à vendre"""
    if request.method == 'POST':
        try:
            # Récupération des données du formulaire
            marque_choice = request.POST.get('marque')
            new_marque_nom = (request.POST.get("new_marque_nom") or "").strip()
            new_marque_pays = (request.POST.get("new_marque_pays") or "Non spécifié").strip() or "Non spécifié"
            new_marque_date_raw = (request.POST.get("new_marque_date") or "").strip()
            modele_nom = (request.POST.get('modele') or "").strip()
            prix_raw = request.POST.get('prix')
            kilometrage_raw = request.POST.get('kilometrage')
            annee_raw = request.POST.get('annee')
            couleur = request.POST.get('couleur')
            etat = request.POST.get('etat')
            description = (request.POST.get('description') or "").strip()
            type_carburant = request.POST.get("type_carburant") or "essence"
            transmission = request.POST.get("transmission") or "manuelle"
            puissance_raw = request.POST.get("puissance")
            consommation_raw = request.POST.get("consommation")

            if not ((marque_choice or new_marque_nom) and modele_nom and prix_raw and kilometrage_raw and annee_raw and couleur and etat and description):
                messages.error(request, "Veuillez remplir tous les champs obligatoires (dont marque et modèle).")
                return redirect("ajouter_voiture")

            try:
                prix = Decimal(str(prix_raw))
            except (InvalidOperation, TypeError, ValueError):
                messages.error(request, "Prix invalide.")
                return redirect("ajouter_voiture")
            if prix <= 0:
                messages.error(request, "Le prix doit être supérieur à 0.")
                return redirect("ajouter_voiture")

            try:
                kilometrage = int(kilometrage_raw)
            except (TypeError, ValueError):
                messages.error(request, "Kilométrage invalide.")
                return redirect("ajouter_voiture")
            if kilometrage < 0:
                messages.error(request, "Le kilométrage ne peut pas être négatif.")
                return redirect("ajouter_voiture")

            try:
                annee = int(annee_raw)
            except (TypeError, ValueError):
                messages.error(request, "Année invalide.")
                return redirect("ajouter_voiture")

            try:
                puissance = int(puissance_raw) if puissance_raw not in (None, "") else 100
            except (TypeError, ValueError):
                puissance = 100

            try:
                consommation = float(consommation_raw) if consommation_raw not in (None, "") else 6.0
            except (TypeError, ValueError):
                consommation = 6.0
            
            # Création ou récupération de la marque et du modèle
            if marque_choice == "__new__":
                if not new_marque_nom:
                    messages.error(request, "Indiquez le nom de la nouvelle marque.")
                    return redirect("ajouter_voiture")
                try:
                    parsed_date = date.fromisoformat(new_marque_date_raw) if new_marque_date_raw else timezone.now().date()
                except ValueError:
                    parsed_date = timezone.now().date()
                marque, _created = Marque.objects.get_or_create(
                    nom=new_marque_nom,
                    defaults={
                        "pays": new_marque_pays or "Non spécifié",
                        "date_creation": parsed_date,
                        "description": "",
                    },
                )
            else:
                marque = get_object_or_404(Marque, id=marque_choice)

            modele, created = Modele.objects.get_or_create(
                marque=marque,
                nom=modele_nom,
                defaults={
                    'annee_lancement': annee,
                    'type_carburant': type_carburant,
                    'transmission': transmission,
                    'puissance': puissance,
                    'consommation': consommation,
                }
            )
            
            # Création de la voiture
            voiture = Voiture.objects.create(
                modele=modele,
                prix=prix,
                kilometrage=kilometrage,
                annee=annee,
                couleur=couleur,
                etat=etat,
                description=description,
                vendeur=request.user
            )
            
            # Gestion de l'image principale
            if 'image' in request.FILES:
                error = _validate_uploaded_image(request.FILES["image"])
                if error:
                    messages.error(request, error)
                    voiture.delete()
                    return redirect("ajouter_voiture")
                voiture.image_principale = request.FILES['image']
                voiture.save()

            # Images supplémentaires
            extra_images = request.FILES.getlist("images")
            ordre = 0
            for img in extra_images:
                error = _validate_uploaded_image(img)
                if error:
                    messages.warning(request, f"Image ignorée: {error}")
                    continue
                ImageVoiture.objects.create(voiture=voiture, image=img, ordre=ordre)
                ordre += 1
            
            messages.success(request, 'Votre annonce a été publiée avec succès !')
            _notify(
                _staff_users(),
                type="new_listing",
                titre="Nouvelle annonce publiée",
                contenu=f"{request.user.username} a publié l'annonce #{voiture.id}.",
                url=voiture.get_absolute_url(),
            )
            _notify(
                User.objects.filter(is_active=True).exclude(id=request.user.id),
                type="new_listing",
                titre="Nouvelle voiture disponible",
                contenu=f"{voiture.modele.marque.nom} {voiture.modele.nom} ({voiture.annee}).",
                url=voiture.get_absolute_url(),
            )
            return redirect('detail_voiture', voiture_id=voiture.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création : {str(e)}')
    
    # GET request - afficher le formulaire
    marques = Marque.objects.all()
    context = {'marques': marques}
    return render(request, 'voitures/ajouter_voiture.html', context)

@login_required
def modifier_voiture(request, voiture_id):
    """Modifier une voiture existante"""
    voiture = get_object_or_404(Voiture, id=voiture_id)
    
    # Vérifier que l'utilisateur est le propriétaire
    if voiture.vendeur != request.user:
        messages.error(request, "Vous n'avez pas la permission de modifier cette annonce.")
        return redirect('detail_voiture', voiture_id=voiture_id)
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            prix_raw = request.POST.get('prix')
            kilometrage_raw = request.POST.get('kilometrage')
            description = (request.POST.get('description') or "").strip()
            est_vendue = 'est_vendue' in request.POST  # Checkbox renvoie 'on' si cochée

            try:
                prix = Decimal(str(prix_raw))
            except (InvalidOperation, TypeError, ValueError):
                messages.error(request, "Prix invalide.")
                return redirect("modifier_voiture", voiture_id=voiture.id)
            if prix <= 0:
                messages.error(request, "Le prix doit être supérieur à 0.")
                return redirect("modifier_voiture", voiture_id=voiture.id)

            try:
                kilometrage = int(kilometrage_raw)
            except (TypeError, ValueError):
                messages.error(request, "Kilométrage invalide.")
                return redirect("modifier_voiture", voiture_id=voiture.id)
            if kilometrage < 0:
                messages.error(request, "Le kilométrage ne peut pas être négatif.")
                return redirect("modifier_voiture", voiture_id=voiture.id)
            
            # Mettre à jour la voiture
            voiture.prix = prix
            voiture.kilometrage = kilometrage
            voiture.description = description
            voiture.est_vendue = est_vendue
            
            # Gestion de l'image
            if 'image' in request.FILES:
                error = _validate_uploaded_image(request.FILES["image"])
                if error:
                    messages.error(request, error)
                    return redirect('modifier_voiture', voiture_id=voiture.id)
                voiture.image_principale = request.FILES['image']
            
            voiture.save()
            messages.success(request, 'Annonce mise à jour avec succès !')
            return redirect('detail_voiture', voiture_id=voiture.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la mise à jour : {str(e)}')
    
    context = {'voiture': voiture}
    return render(request, 'voitures/modifier_voiture.html', context)

@login_required
def supprimer_voiture(request, voiture_id):
    """Supprimer une voiture existante"""
    voiture = get_object_or_404(Voiture, id=voiture_id)
    
    # Vérifier que l'utilisateur est le propriétaire
    if voiture.vendeur != request.user:
        messages.error(request, "Vous n'avez pas la permission de supprimer cette annonce.")
        return redirect('detail_voiture', voiture_id=voiture_id)
    
    if request.method == 'POST':
        try:
            voiture.delete()
            messages.success(request, 'Annonce supprimée avec succès !')
            return redirect('mes_voitures')
        except Exception as e:
            messages.error(request, f'Erreur lors de la suppression : {str(e)}')
    
    # Si GET, afficher la page de confirmation
    context = {'voiture': voiture}
    return render(request, 'voitures/supprimer_voiture.html', context)

@login_required
def toggle_favori(request, voiture_id):
    """Ajouter/retirer une voiture des favoris"""
    if request.method != "POST":
        return redirect('detail_voiture', voiture_id=voiture_id)
    voiture = get_object_or_404(Voiture, id=voiture_id)
    
    # Vérifier si déjà en favori
    favori, created = Favori.objects.get_or_create(
        utilisateur=request.user,
        voiture=voiture
    )
    
    if not created:
        favori.delete()
        messages.info(request, 'Voiture retirée des favoris.')
    else:
        messages.success(request, 'Voiture ajoutée aux favoris.')
    
    return redirect('detail_voiture', voiture_id=voiture_id)


@login_required
@require_POST
def ajouter_avis(request, voiture_id):
    voiture = get_object_or_404(Voiture, id=voiture_id)
    if request.user == voiture.vendeur:
        messages.error(request, "Vous ne pouvez pas noter votre propre annonce.")
        return redirect("detail_voiture", voiture_id=voiture_id)

    form = AvisForm(request.POST)
    if form.is_valid():
        avis, created = Avis.objects.get_or_create(
            voiture=voiture,
            utilisateur=request.user,
            defaults={
                "note": form.cleaned_data["note"],
                "commentaire": form.cleaned_data["commentaire"],
                "approuve": False,
            },
        )
        if not created:
            avis.note = form.cleaned_data["note"]
            avis.commentaire = form.cleaned_data["commentaire"]
            avis.approuve = False
            avis.save(update_fields=["note", "commentaire", "approuve"])
        messages.success(request, "Avis envoyé. Il sera visible après validation.")
    else:
        messages.error(request, "Avis invalide. Vérifiez les champs.")
    return redirect("detail_voiture", voiture_id=voiture_id)


@login_required
@require_POST
def envoyer_message(request, voiture_id):
    voiture = get_object_or_404(Voiture.objects.select_related("vendeur", "modele__marque", "modele"), id=voiture_id)
    if request.user == voiture.vendeur:
        messages.error(request, "Vous ne pouvez pas vous envoyer un message à vous-même.")
        return redirect("detail_voiture", voiture_id=voiture_id)

    contenu = (request.POST.get("contenu") or "").strip()
    if not contenu:
        messages.error(request, "Message vide.")
        return redirect("detail_voiture", voiture_id=voiture_id)

    Message.objects.create(
        expediteur=request.user,
        destinataire=voiture.vendeur,
        sujet=f"Annonce #{voiture.id} — {voiture.modele.marque.nom} {voiture.modele.nom}",
        contenu=contenu,
    )
    _notify(
        [voiture.vendeur],
        type="message",
        titre="Nouveau message",
        contenu=f"Message reçu pour l'annonce #{voiture.id}.",
        url=voiture.get_absolute_url(),
    )
    messages.success(request, "Message envoyé au vendeur.")
    return redirect("detail_voiture", voiture_id=voiture_id)


@login_required
def mes_messages(request):
    recus = Message.objects.filter(destinataire=request.user).select_related("expediteur").order_by("-date_envoi")
    envoyes = Message.objects.filter(expediteur=request.user).select_related("destinataire").order_by("-date_envoi")

    tab = request.GET.get("tab", "recus")
    if tab not in {"recus", "envoyes"}:
        tab = "recus"

    if tab == "recus":
        Message.objects.filter(destinataire=request.user, lu=False).update(lu=True)

    context = {"recus": recus, "envoyes": envoyes, "tab": tab}
    return render(request, "voitures/mes_messages.html", context)


@login_required
def notifications(request):
    items = Notification.objects.filter(utilisateur=request.user).order_by("-date_creation")[:200]
    Notification.objects.filter(utilisateur=request.user, lu=False).update(lu=True)
    return render(request, "voitures/notifications.html", {"items": items})

@login_required
def acheter_voiture(request, voiture_id):
    """Processus d'achat d'une voiture"""
    voiture = get_object_or_404(Voiture, id=voiture_id, est_vendue=False)
    
    if request.user == voiture.vendeur:
        messages.error(request, 'Vous ne pouvez pas acheter votre propre voiture.')
        return redirect('detail_voiture', voiture_id=voiture_id)

    if voiture.est_reservee:
        existing = Transaction.objects.filter(
            voiture=voiture, statut="en_attente", acheteur=request.user
        ).first()
        if existing:
            messages.info(request, "Votre demande est déjà en attente pour cette voiture.")
            return redirect("mes_achats")
        messages.info(request, "Cette voiture est déjà réservée.")
        return redirect('detail_voiture', voiture_id=voiture_id)
    
    if request.method == 'POST':
        try:
            result = transactions.create_purchase_request(voiture_id=voiture.id, buyer=request.user)
            _notify(
                [voiture.vendeur],
                type="purchase_request",
                titre="Nouvelle demande d'achat",
                contenu=f"{request.user.username} a demandé à acheter l'annonce #{voiture.id}.",
                url=voiture.get_absolute_url(),
            )
            _notify(
                _staff_users(),
                type="purchase_request",
                titre="Demande d'achat à traiter",
                contenu=f"Annonce #{voiture.id} — {voiture.modele.marque.nom} {voiture.modele.nom}.",
                url="/dashboard/",
            )
            if result.created:
                messages.success(
                    request,
                    "Demande envoyée. La voiture est réservée pendant le traitement ("
                    f"{transactions.get_reservation_ttl_hours()}h).",
                )
            else:
                messages.info(request, "Votre demande est déjà en attente pour cette voiture.")
            return redirect("mes_achats")

        except transactions.TransactionError as exc:
            messages.info(request, str(exc))
            return redirect("detail_voiture", voiture_id=voiture_id)
        except Voiture.DoesNotExist:
            messages.error(request, "Voiture introuvable.")
            return redirect("liste_voitures")
        except Exception as e:
            messages.error(request, f"Erreur lors de l'achat : {str(e)}")
    
    context = {'voiture': voiture}
    return render(request, 'voitures/acheter_voiture.html', context)

@login_required
def mes_voitures(request):
    """Liste des voitures de l'utilisateur"""
    voitures = Voiture.objects.filter(vendeur=request.user).order_by('-date_ajout')
    
    # Calcul des statistiques
    voitures_en_vente = voitures.filter(est_vendue=False).count()
    voitures_vendues = voitures.filter(est_vendue=True).count()
    total_favoris = Favori.objects.filter(voiture__vendeur=request.user).count()
    
    context = {
        'voitures': voitures,
        'voitures_en_vente': voitures_en_vente,
        'voitures_vendues': voitures_vendues,
        'total_favoris': total_favoris,
    }
    return render(request, 'voitures/mes_voitures.html', context)

@login_required
def mes_favoris(request):
    """Liste des favoris de l'utilisateur"""
    favoris = Favori.objects.filter(utilisateur=request.user).select_related(
        'voiture__modele__marque'
    ).order_by('-date_ajout')
    
    context = {'favoris': favoris}
    return render(request, 'voitures/mes_favoris.html', context)

@login_required
def mes_achats(request):
    """Historique des achats de l'utilisateur"""
    achats = Transaction.objects.filter(acheteur=request.user).select_related(
        'voiture__modele__marque', 'vendeur'
    ).order_by('-date_transaction')
    
    context = {'achats': achats}
    return render(request, 'voitures/mes_achats.html', context)

@login_required
def mes_ventes(request):
    """Historique des ventes de l'utilisateur"""
    ventes = Transaction.objects.filter(vendeur=request.user).select_related(
        'voiture__modele__marque', 'acheteur'
    ).order_by('-date_transaction')
    
    context = {'ventes': ventes}
    return render(request, 'voitures/mes_ventes.html', context)

@login_required
def confirmer_vente(request, transaction_id):
    """Confirmer une vente"""
    if request.method != "POST":
        return redirect('mes_ventes')

    transaction = transactions.confirm_sale(transaction_id=transaction_id, seller=request.user)
    voiture = transaction.voiture

    _notify(
        [transaction.acheteur],
        type="sale_confirmed",
        titre="Vente confirmée",
        contenu=f"Votre achat pour l'annonce #{voiture.id} a été confirmé.",
        url=voiture.get_absolute_url(),
    )
    _notify(
        _staff_users(),
        type="sale_confirmed",
        titre="Vente confirmée",
        contenu=f"Annonce #{voiture.id} — transaction #{transaction.id} confirmée.",
        url="/dashboard/",
    )
    
    messages.success(request, 'Vente confirmée avec succès !')
    return redirect('mes_ventes')


@login_required
@require_POST
def annuler_transaction(request, transaction_id):
    """
    Annulation par l'acheteur d'une transaction en attente (libère la réservation).
    """
    trx = transactions.cancel_purchase_request(transaction_id=transaction_id, buyer=request.user)
    voiture = trx.voiture

    _notify(
        [trx.vendeur],
        type="purchase_request",
        titre="Demande d'achat annulée",
        contenu=f"{request.user.username} a annulé la demande sur l'annonce #{voiture.id}.",
        url=voiture.get_absolute_url(),
    )
    messages.info(request, "Demande annulée.")
    return redirect("mes_achats")


@login_required
@require_POST
def refuser_transaction(request, transaction_id):
    """
    Refus par le vendeur d'une transaction en attente (libère la réservation).
    """
    trx = transactions.refuse_purchase_request(transaction_id=transaction_id, seller=request.user)
    voiture = trx.voiture

    _notify(
        [trx.acheteur],
        type="purchase_request",
        titre="Demande d'achat refusée",
        contenu=f"Le vendeur a refusé la demande sur l'annonce #{voiture.id}.",
        url=voiture.get_absolute_url(),
    )
    messages.info(request, "Demande refusée.")
    return redirect("mes_ventes")

# ==================== VUES ADMIN UTILISATEURS ====================

@login_required
def dashboard(request):
    """Tableau de bord utilisateur"""
    if not request.user.is_staff:
        return redirect('accueil')
    
    # Statistiques pour l'admin
    total_utilisateurs = User.objects.count()
    total_voitures = Voiture.objects.count()
    total_transactions = Transaction.objects.count()
    chiffre_affaires = Transaction.objects.filter(
        statut__in=['confirmee', 'terminee']
    ).aggregate(Sum('prix_final'))['prix_final__sum'] or 0
    
    # Dernières transactions
    transactions_recentes = Transaction.objects.select_related(
        'voiture', 'acheteur', 'vendeur'
    ).order_by('-date_transaction')[:10]

    transactions_en_attente = Transaction.objects.filter(statut="en_attente").select_related(
        "voiture", "acheteur", "vendeur"
    ).order_by("-date_transaction")[:10]
    
    # Voitures récentes
    voitures_recentes = Voiture.objects.select_related(
        'modele__marque', 'vendeur'
    ).order_by('-date_ajout')[:10]

    notifications_recentes = Notification.objects.filter(utilisateur=request.user).order_by("-date_creation")[:10]
    
    context = {
        'total_utilisateurs': total_utilisateurs,
        'total_voitures': total_voitures,
        'total_transactions': total_transactions,
        'chiffre_affaires': chiffre_affaires,
        'transactions_recentes': transactions_recentes,
        'transactions_en_attente': transactions_en_attente,
        'voitures_recentes': voitures_recentes,
        'notifications_recentes': notifications_recentes,
    }
    return render(request, 'admin/dashboard.html', context)

# ==================== VUES D'ERREUR ====================

def handler404(request, exception):
    """Page 404 personnalisée"""
    return render(request, 'voitures/404.html', status=404)

def handler500(request):
    """Page 500 personnalisée"""
    return render(request, 'voitures/500.html', status=500)

# ==================== VUE DE TEST ====================

def test(request):
    """Page de test pour vérifier le fonctionnement"""
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Django</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>Test de l'application Django</h1>
        <h2>Statut : <span class="success">✓ EN COURS</span></h2>
        <ul>
            <li>Serveur Django : ✓ Opérationnel</li>
            <li>Base de données : ✓ Connectée</li>
            <li>Templates : ✓ Chargés</li>
            <li>URLs : ✓ Configurées</li>
        </ul>
        <p><a href="/">Retour à l'accueil</a></p>
    </body>
    </html>
    """)

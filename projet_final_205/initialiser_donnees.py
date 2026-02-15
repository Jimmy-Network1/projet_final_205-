import os
import sys
import django
from datetime import date

# Configuration de Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from voitures.models import Marque, Modele, Voiture
from django.contrib.auth.models import User

DEMO_ACCOUNTS = {
    "admin": {
        "email": "admin@automarket.com",
        "password": "Admin123!",
        "first_name": "Admin",
        "last_name": "AutoMarket",
        "is_staff": True,
        "is_superuser": True,
    },
    "vendeur": {
        "email": "vendeur@automarket.com",
        "password": "Vendeur123!",
        "first_name": "Jean",
        "last_name": "Dupont",
        "is_staff": False,
        "is_superuser": False,
    },
    "acheteur": {
        "email": "acheteur@automarket.com",
        "password": "Acheteur123!",
        "first_name": "Marie",
        "last_name": "Martin",
        "is_staff": False,
        "is_superuser": False,
    },
}


def creer_marques():
    marques_data = [
        {'nom': 'Renault', 'pays': 'France', 'date_creation': date(1899, 2, 25)},
        {'nom': 'Peugeot', 'pays': 'France', 'date_creation': date(1810, 9, 26)},
        {'nom': 'Citroën', 'pays': 'France', 'date_creation': date(1919, 6, 4)},
        {'nom': 'Volkswagen', 'pays': 'Allemagne', 'date_creation': date(1937, 5, 28)},
        {'nom': 'BMW', 'pays': 'Allemagne', 'date_creation': date(1916, 3, 7)},
        {'nom': 'Mercedes-Benz', 'pays': 'Allemagne', 'date_creation': date(1926, 6, 28)},
        {'nom': 'Toyota', 'pays': 'Japon', 'date_creation': date(1937, 8, 28)},
        {'nom': 'Ford', 'pays': 'États-Unis', 'date_creation': date(1903, 6, 16)},
    ]
    
    for data in marques_data:
        Marque.objects.get_or_create(**data)
    
    print("Marques créées avec succès!")

def creer_modeles():
    marques = Marque.objects.all()
    
    modeles_data = [
        {'marque': 'Renault', 'nom': 'Clio', 'annee_lancement': 1990, 'type_carburant': 'essence', 'transmission': 'manuelle', 'puissance': 90, 'consommation': 5.2},
        {'marque': 'Peugeot', 'nom': '208', 'annee_lancement': 2012, 'type_carburant': 'diesel', 'transmission': 'manuelle', 'puissance': 75, 'consommation': 3.8},
        {'marque': 'Citroën', 'nom': 'C3', 'annee_lancement': 2002, 'type_carburant': 'essence', 'transmission': 'automatique', 'puissance': 82, 'consommation': 5.8},
        {'marque': 'Volkswagen', 'nom': 'Golf', 'annee_lancement': 1974, 'type_carburant': 'diesel', 'transmission': 'manuelle', 'puissance': 115, 'consommation': 4.5},
        {'marque': 'BMW', 'nom': 'Série 3', 'annee_lancement': 1975, 'type_carburant': 'essence', 'transmission': 'automatique', 'puissance': 184, 'consommation': 6.8},
        {'marque': 'Mercedes-Benz', 'nom': 'Classe A', 'annee_lancement': 1997, 'type_carburant': 'essence', 'transmission': 'automatique', 'puissance': 163, 'consommation': 6.5},
        {'marque': 'Toyota', 'nom': 'Yaris', 'annee_lancement': 1999, 'type_carburant': 'hybride', 'transmission': 'automatique', 'puissance': 116, 'consommation': 3.8},
        {'marque': 'Ford', 'nom': 'Fiesta', 'annee_lancement': 1976, 'type_carburant': 'essence', 'transmission': 'manuelle', 'puissance': 100, 'consommation': 5.4},
    ]
    
    for data in modeles_data:
        marque = Marque.objects.get(nom=data.pop('marque'))
        Modele.objects.get_or_create(marque=marque, **data)
    
    print("Modèles créés avec succès!")

def creer_comptes_demo():
    users = {}
    for username, data in DEMO_ACCOUNTS.items():
        password = data["password"]
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": data["email"],
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "is_staff": data["is_staff"],
                "is_superuser": data["is_superuser"],
            },
        )

        changed = False
        for field in ("email", "first_name", "last_name", "is_staff", "is_superuser"):
            value = data[field]
            if getattr(user, field) != value:
                setattr(user, field, value)
                changed = True

        user.set_password(password)
        user.is_active = True
        user.save()

        label = "créé" if created else "mis à jour"
        print(f"Compte {label}: {username} / {password}")
        users[username] = user

    return users

def creer_voitures_test():
    user = User.objects.get(username='vendeur')
    
    voitures_data = [
        {
            'modele': Modele.objects.get(marque__nom='Renault', nom='Clio'),
            'prix': 12500,
            'kilometrage': 45000,
            'annee': 2020,
            'couleur': 'blanc',
            'etat': 'occasion',
            'description': 'Clio en excellent état, très bien entretenue.',
            'vendeur': user
        },
        {
            'modele': Modele.objects.get(marque__nom='Peugeot', nom='208'),
            'prix': 18500,
            'kilometrage': 15000,
            'annee': 2021,
            'couleur': 'gris',
            'etat': 'occasion',
            'description': 'Peugeot 208 presque neuve, garantie constructeur.',
            'vendeur': user
        },
        {
            'modele': Modele.objects.get(marque__nom='BMW', nom='Série 3'),
            'prix': 32500,
            'kilometrage': 75000,
            'annee': 2019,
            'couleur': 'noir',
            'etat': 'occasion',
            'description': 'BMW Série 3 full options, très bon état général.',
            'vendeur': user
        },
    ]
    
    for data in voitures_data:
        Voiture.objects.get_or_create(**data)
    
    print("Voitures de test créées avec succès!")

if __name__ == '__main__':
    print("Initialisation des données...")
    creer_marques()
    creer_modeles()
    creer_comptes_demo()
    creer_voitures_test()
    print("Initialisation terminée!")

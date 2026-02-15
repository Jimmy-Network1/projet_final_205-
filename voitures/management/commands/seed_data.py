# voitures/management/commands/seed_data.py
import os
import django
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from voitures.models import Marque, Modele, Voiture
from django.utils import timezone
import datetime

class Command(BaseCommand):
    help = 'Remplit la base de données avec des données de test'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Création des données par défaut...')
        
       
        
        # Créer un utilisateur vendeur
        vendeur, created = User.objects.get_or_create(
            username='vendeur',
            defaults={
                'email': 'vendeur@automarket.com',
                'first_name': 'Jean',
                'last_name': 'Dupont'
            }
        )
        if created:
            vendeur.set_password('vendeur123')
            vendeur.save()
            self.stdout.write(self.style.SUCCESS('✓ Utilisateur vendeur créé'))
        
        # Liste des marques à créer
        marques_data = [
            {
                'nom': 'Renault',
                'pays': 'France',
                'date_creation': datetime.date(1899, 2, 25),
                'description': 'Constructeur automobile français fondé en 1899.'
            },
            {
                'nom': 'Peugeot',
                'pays': 'France',
                'date_creation': datetime.date(1810, 9, 26),
                'description': 'Marque automobile française créée en 1810.'
            },
            {
                'nom': 'Citroën',
                'pays': 'France',
                'date_creation': datetime.date(1919, 6, 4),
                'description': 'Constructeur automobile français fondé en 1919.'
            },
            {
                'nom': 'Volkswagen',
                'pays': 'Allemagne',
                'date_creation': datetime.date(1937, 5, 28),
                'description': 'Constructeur automobile allemand fondé en 1937.'
            },
            {
                'nom': 'BMW',
                'pays': 'Allemagne',
                'date_creation': datetime.date(1916, 3, 7),
                'description': 'Constructeur allemand de voitures et motos.'
            },
            {
                'nom': 'Mercedes-Benz',
                'pays': 'Allemagne',
                'date_creation': datetime.date(1926, 6, 28),
                'description': 'Marque automobile allemande de luxe.'
            },
            {
                'nom': 'Toyota',
                'pays': 'Japon',
                'date_creation': datetime.date(1937, 8, 28),
                'description': 'Constructeur automobile japonais.'
            },
            {
                'nom': 'Ford',
                'pays': 'États-Unis',
                'date_creation': datetime.date(1903, 6, 16),
                'description': 'Constructeur automobile américain.'
            },
            {
                'nom': 'Audi',
                'pays': 'Allemagne',
                'date_creation': datetime.date(1909, 7, 16),
                'description': 'Marque allemande de voitures haut de gamme.'
            },
            {
                'nom': 'Tesla',
                'pays': 'États-Unis',
                'date_creation': datetime.date(2003, 7, 1),
                'description': 'Constructeur américain de voitures électriques.'
            }
        ]
        
        marques = {}
        for data in marques_data:
            marque, created = Marque.objects.get_or_create(
                nom=data['nom'],
                defaults=data
            )
            marques[marque.nom] = marque
            if created:
                self.stdout.write(f"✓ Marque {marque.nom} créée")
        
        # Modèles pour chaque marque
        modeles_data = [
            # Renault
            {'marque': marques['Renault'], 'nom': 'Clio', 'annee_lancement': 1990, 
             'type_carburant': 'essence', 'transmission': 'manuelle', 'puissance': 90, 'consommation': 5.2},
            {'marque': marques['Renault'], 'nom': 'Mégane', 'annee_lancement': 1995, 
             'type_carburant': 'diesel', 'transmission': 'manuelle', 'puissance': 110, 'consommation': 4.5},
            {'marque': marques['Renault'], 'nom': 'Captur', 'annee_lancement': 2013, 
             'type_carburant': 'essence', 'transmission': 'automatique', 'puissance': 100, 'consommation': 5.8},
            
            # Peugeot
            {'marque': marques['Peugeot'], 'nom': '208', 'annee_lancement': 2012, 
             'type_carburant': 'essence', 'transmission': 'automatique', 'puissance': 82, 'consommation': 5.0},
            {'marque': marques['Peugeot'], 'nom': '3008', 'annee_lancement': 2009, 
             'type_carburant': 'diesel', 'transmission': 'automatique', 'puissance': 130, 'consommation': 5.5},
            {'marque': marques['Peugeot'], 'nom': '5008', 'annee_lancement': 2009, 
             'type_carburant': 'hybride', 'transmission': 'automatique', 'puissance': 180, 'consommation': 4.2},
            
            # Volkswagen
            {'marque': marques['Volkswagen'], 'nom': 'Golf', 'annee_lancement': 1974, 
             'type_carburant': 'essence', 'transmission': 'manuelle', 'puissance': 115, 'consommation': 5.5},
            {'marque': marques['Volkswagen'], 'nom': 'Passat', 'annee_lancement': 1973, 
             'type_carburant': 'diesel', 'transmission': 'automatique', 'puissance': 150, 'consommation': 5.0},
            {'marque': marques['Volkswagen'], 'nom': 'Tiguan', 'annee_lancement': 2007, 
             'type_carburant': 'essence', 'transmission': 'automatique', 'puissance': 150, 'consommation': 7.2},
            
            # BMW
            {'marque': marques['BMW'], 'nom': 'Série 3', 'annee_lancement': 1975, 
             'type_carburant': 'essence', 'transmission': 'automatique', 'puissance': 184, 'consommation': 6.8},
            {'marque': marques['BMW'], 'nom': 'X5', 'annee_lancement': 1999, 
             'type_carburant': 'diesel', 'transmission': 'automatique', 'puissance': 265, 'consommation': 7.4},
            
            # Toyota
            {'marque': marques['Toyota'], 'nom': 'Yaris', 'annee_lancement': 1999, 
             'type_carburant': 'hybride', 'transmission': 'automatique', 'puissance': 116, 'consommation': 3.8},
            {'marque': marques['Toyota'], 'nom': 'RAV4', 'annee_lancement': 1994, 
             'type_carburant': 'hybride', 'transmission': 'automatique', 'puissance': 222, 'consommation': 5.0},
            
            # Tesla
            {'marque': marques['Tesla'], 'nom': 'Model 3', 'annee_lancement': 2017, 
             'type_carburant': 'electrique', 'transmission': 'automatique', 'puissance': 283, 'consommation': 0},
            {'marque': marques['Tesla'], 'nom': 'Model Y', 'annee_lancement': 2020, 
             'type_carburant': 'electrique', 'transmission': 'automatique', 'puissance': 384, 'consommation': 0},
        ]
        
        modeles = {}
        for data in modeles_data:
            modele, created = Modele.objects.get_or_create(
                marque=data['marque'],
                nom=data['nom'],
                defaults=data
            )
            modeles[f"{data['marque'].nom} {data['nom']}"] = modele
            if created:
                self.stdout.write(f"✓ Modèle {modele} créé")
        
        # Voitures d'exemple
        voitures_data = [
            # Renault Clio - Bon état
            {
                'modele': modeles['Renault Clio'],
                'prix': 12500,
                'kilometrage': 45000,
                'annee': 2020,
                'couleur': 'blanc',
                'etat': 'occasion',
                'description': 'Clio en excellent état, très bien entretenue. 1ère main, livre d\'entretien complet. Clim, GPS, toit ouvrant, jantes alliage. Vendu avec contrôle technique récent.',
                'vendeur': vendeur
            },
            # Renault Mégane - Familiale
            {
                'modele': modeles['Renault Mégane'],
                'prix': 18500,
                'kilometrage': 75000,
                'annee': 2019,
                'couleur': 'gris',
                'etat': 'occasion',
                'description': 'Mégane diesel, économique et confortable. Full options : cuir, sièges chauffants, caméra de recul, régulateur adaptatif. Parfait état.',
                'vendeur': vendeur
            },
            # Peugeot 208 - Citadine récente
            {
                'modele': modeles['Peugeot 208'],
                'prix': 15500,
                'kilometrage': 25000,
                'annee': 2021,
                'couleur': 'rouge',
                'etat': 'occasion',
                'description': 'Peugeot 208 presque neuve, garantie constructeur restante (12 mois). Clim auto, écran tactile, Apple CarPlay/Android Auto. Très peu utilisée.',
                'vendeur': vendeur
            },
            # Peugeot 3008 - SUV familial
            {
                'modele': modeles['Peugeot 3008'],
                'prix': 28500,
                'kilometrage': 40000,
                'annee': 2020,
                'couleur': 'noir',
                'etat': 'occasion',
                'description': 'SUV familial spacieux, très bon état général. Pack GT avec jantes 19", intérieur cuir, toit panoramique. Diesel économique.',
                'vendeur': vendeur
            },
            # BMW Série 3 - Berline prestige
            {
                'modele': modeles['BMW Série 3'],
                'prix': 32500,
                'kilometrage': 35000,
                'annee': 2021,
                'couleur': 'bleu',
                'etat': 'occasion',
                'description': 'BMW Série 3 full options, cuir, écran tactile 10", sièges massants, Harman Kardon. Conduite impeccable. Entretien BMW.',
                'vendeur': vendeur
            },
            # Volkswagen Golf - Compacte polyvalente
            {
                'modele': modeles['Volkswagen Golf'],
                'prix': 21500,
                'kilometrage': 55000,
                'annee': 2020,
                'couleur': 'argent',
                'etat': 'occasion',
                'description': 'Golf 8 en excellent état. Pack R-Line, LED matrix, assistances nombreuses. Consommation faible. 2 clés.',
                'vendeur': vendeur
            },
            # Toyota Yaris - Hybride économique
            {
                'modele': modeles['Toyota Yaris'],
                'prix': 19500,
                'kilometrage': 30000,
                'annee': 2022,
                'couleur': 'vert',
                'etat': 'occasion',
                'description': 'Yaris hybride, très économique (3,8L/100km). Garantie Toyota 5 ans. Pack Design avec jantes 17". Comme neuve.',
                'vendeur': vendeur
            },
            # Tesla Model 3 - Électrique
            {
                'modele': modeles['Tesla Model 3'],
                'prix': 42500,
                'kilometrage': 15000,
                'annee': 2023,
                'couleur': 'noir',
                'etat': 'occasion',
                'description': 'Tesla Model 3 Standard Range Plus. Autonomie 448km, superchargeur inclus. Toit vitré, intérieur vegan. Garantie batterie.',
                'vendeur': vendeur
            },
            # BMW X5 - SUV luxe
            {
                'modele': modeles['BMW X5'],
                'prix': 49500,
                'kilometrage': 60000,
                'annee': 2019,
                'couleur': 'gris',
                'etat': 'occasion',
                'description': 'BMW X5 xDrive30d M Sport. V8 biturbo, intérieur cuir merino, air suspension, head-up display. Véhicule prestige.',
                'vendeur': vendeur
            },
            # Volkswagen Tiguan - SUV compact
            {
                'modele': modeles['Volkswagen Tiguan'],
                'prix': 27500,
                'kilometrage': 45000,
                'annee': 2021,
                'couleur': 'blanc',
                'etat': 'occasion',
                'description': 'Tiguan R-Line, 4x4, sièges chauffants, écran 9,2". 7 places. Parfait pour famille. Contrôle technique OK.',
                'vendeur': vendeur
            },
        ]
        
        for i, data in enumerate(voitures_data):
            voiture, created = Voiture.objects.get_or_create(
                modele=data['modele'],
                annee=data['annee'],
                kilometrage=data['kilometrage'],
                defaults=data
            )
            if created:
                voiture.moderation_status = "approved"
                voiture.moderated_at = timezone.now()
                voiture.save(update_fields=["moderation_status", "moderated_at"])
                self.stdout.write(f"✓ Voiture {voiture} créée")
        
        self.stdout.write(self.style.SUCCESS('✓ Données par défaut créées avec succès !'))
        self.stdout.write('\nComptes de test créés :')
        self.stdout.write('  Admin: username=admin / password=admin123')
        self.stdout.write('  Vendeur: username=vendeur / password=vendeur123')

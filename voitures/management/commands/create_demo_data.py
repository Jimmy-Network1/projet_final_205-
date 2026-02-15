# voitures/management/commands/create_demo_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from voitures.models import Marque, Modele, Voiture
import datetime

class Command(BaseCommand):
    help = 'Crée des données de démonstration pour le site'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Création des données de démonstration...'))
        
        # Créer les utilisateurs de démo
        users_data = [
            {
                'username': 'admin',
                'email': 'admin@automarket.com',
                'password': 'Admin123!',
                'is_staff': True,
                'is_superuser': True,
                'first_name': 'Administrateur',
                'last_name': 'System'
            },
            {
                'username': 'vendeur',
                'email': 'vendeur@automarket.com',
                'password': 'Vendeur123!',
                'first_name': 'Jean',
                'last_name': 'Dupont'
            },
            {
                'username': 'acheteur',
                'email': 'acheteur@automarket.com',
                'password': 'Acheteur123!',
                'first_name': 'Marie',
                'last_name': 'Martin'
            },
            {
                'username': 'client1',
                'email': 'client1@automarket.com',
                'password': 'Client123!',
                'first_name': 'Pierre',
                'last_name': 'Durand'
            },
            {
                'username': 'client2',
                'email': 'client2@automarket.com',
                'password': 'Client123!',
                'first_name': 'Sophie',
                'last_name': 'Leroy'
            },
        ]
        
        for user_data in users_data:
            username = user_data.pop('username')
            password = user_data.pop('password')
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults=user_data
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f"✓ Utilisateur {username} créé")
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(users_data)} utilisateurs créés'))
        
        # Créer les marques
        marques_data = [
            {'nom': 'Renault', 'pays': 'France', 'date_creation': datetime.date(1899, 2, 25)},
            {'nom': 'Peugeot', 'pays': 'France', 'date_creation': datetime.date(1810, 9, 26)},
            {'nom': 'Citroën', 'pays': 'France', 'date_creation': datetime.date(1919, 6, 4)},
            {'nom': 'Volkswagen', 'pays': 'Allemagne', 'date_creation': datetime.date(1937, 5, 28)},
            {'nom': 'BMW', 'pays': 'Allemagne', 'date_creation': datetime.date(1916, 3, 7)},
            {'nom': 'Mercedes', 'pays': 'Allemagne', 'date_creation': datetime.date(1926, 6, 28)},
            {'nom': 'Toyota', 'pays': 'Japon', 'date_creation': datetime.date(1937, 8, 28)},
            {'nom': 'Ford', 'pays': 'États-Unis', 'date_creation': datetime.date(1903, 6, 16)},
            {'nom': 'Audi', 'pays': 'Allemagne', 'date_creation': datetime.date(1909, 7, 16)},
            {'nom': 'Tesla', 'pays': 'États-Unis', 'date_creation': datetime.date(2003, 7, 1)},
        ]
        
        marques = {}
        for data in marques_data:
            marque, created = Marque.objects.get_or_create(nom=data['nom'], defaults=data)
            marques[marque.nom] = marque
            if created:
                self.stdout.write(f"  ✓ Marque {marque.nom}")
        
        # Créer les modèles
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
            
            # Volkswagen
            {'marque': marques['Volkswagen'], 'nom': 'Golf', 'annee_lancement': 1974, 
             'type_carburant': 'essence', 'transmission': 'manuelle', 'puissance': 115, 'consommation': 5.5},
            {'marque': marques['Volkswagen'], 'nom': 'Passat', 'annee_lancement': 1973, 
             'type_carburant': 'diesel', 'transmission': 'automatique', 'puissance': 150, 'consommation': 5.0},
            
            # BMW
            {'marque': marques['BMW'], 'nom': 'Série 3', 'annee_lancement': 1975, 
             'type_carburant': 'essence', 'transmission': 'automatique', 'puissance': 184, 'consommation': 6.8},
            {'marque': marques['BMW'], 'nom': 'X5', 'annee_lancement': 1999, 
             'type_carburant': 'diesel', 'transmission': 'automatique', 'puissance': 265, 'consommation': 7.4},
            
            # Toyota
            {'marque': marques['Toyota'], 'nom': 'Yaris', 'annee_lancement': 1999, 
             'type_carburant': 'hybride', 'transmission': 'automatique', 'puissance': 116, 'consommation': 3.8},
            
            # Tesla
            {'marque': marques['Tesla'], 'nom': 'Model 3', 'annee_lancement': 2017, 
             'type_carburant': 'electrique', 'transmission': 'automatique', 'puissance': 283, 'consommation': 0},
        ]
        
        for data in modeles_data:
            modele, created = Modele.objects.get_or_create(
                marque=data['marque'],
                nom=data['nom'],
                defaults=data
            )
            if created:
                self.stdout.write(f"  ✓ Modèle {modele.marque.nom} {modele.nom}")
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(modeles_data)} modèles créés'))
        
        # Créer des voitures (10 voitures)
        vendeurs = User.objects.filter(username__in=['vendeur', 'client1', 'client2'])
        voitures_data = [
            # Renault Clio
            {
                'modele': Modele.objects.get(nom='Clio'),
                'prix': 12500,
                'kilometrage': 45000,
                'annee': 2020,
                'couleur': 'blanc',
                'etat': 'occasion',
                'description': 'Clio en excellent état, très bien entretenue. 1ère main, livre d\'entretien complet.',
                'vendeur': vendeurs[0]
            },
            # Renault Mégane
            {
                'modele': Modele.objects.get(nom='Mégane'),
                'prix': 18500,
                'kilometrage': 75000,
                'annee': 2019,
                'couleur': 'gris',
                'etat': 'occasion',
                'description': 'Mégane diesel, économique et confortable. Full options.',
                'vendeur': vendeurs[0]
            },
            # Peugeot 208
            {
                'modele': Modele.objects.get(nom='208'),
                'prix': 15500,
                'kilometrage': 25000,
                'annee': 2021,
                'couleur': 'rouge',
                'etat': 'occasion',
                'description': 'Peugeot 208 presque neuve, garantie constructeur restante.',
                'vendeur': vendeurs[0]
            },
            # Volkswagen Golf
            {
                'modele': Modele.objects.get(nom='Golf'),
                'prix': 21500,
                'kilometrage': 55000,
                'annee': 2020,
                'couleur': 'argent',
                'etat': 'occasion',
                'description': 'Golf 8 en excellent état. Pack R-Line.',
                'vendeur': vendeurs[1]
            },
            # BMW Série 3
            {
                'modele': Modele.objects.get(nom='Série 3'),
                'prix': 32500,
                'kilometrage': 35000,
                'annee': 2021,
                'couleur': 'bleu',
                'etat': 'occasion',
                'description': 'BMW Série 3 full options, cuir, écran tactile.',
                'vendeur': vendeurs[1]
            },
            # Toyota Yaris
            {
                'modele': Modele.objects.get(nom='Yaris'),
                'prix': 19500,
                'kilometrage': 30000,
                'annee': 2022,
                'couleur': 'vert',
                'etat': 'occasion',
                'description': 'Yaris hybride, très économique. Garantie Toyota.',
                'vendeur': vendeurs[2]
            },
            # Tesla Model 3
            {
                'modele': Modele.objects.get(nom='Model 3'),
                'prix': 42500,
                'kilometrage': 15000,
                'annee': 2023,
                'couleur': 'noir',
                'etat': 'occasion',
                'description': 'Tesla Model 3 Standard Range Plus. Autonomie 448km.',
                'vendeur': vendeurs[2]
            },
            # Peugeot 3008
            {
                'modele': Modele.objects.get(nom='3008'),
                'prix': 28500,
                'kilometrage': 40000,
                'annee': 2020,
                'couleur': 'noir',
                'etat': 'occasion',
                'description': 'SUV familial spacieux, très bon état général.',
                'vendeur': vendeurs[0]
            },
            # Renault Captur
            {
                'modele': Modele.objects.get(nom='Captur'),
                'prix': 19500,
                'kilometrage': 35000,
                'annee': 2021,
                'couleur': 'bleu',
                'etat': 'occasion',
                'description': 'Captur crossback, idéal pour la ville.',
                'vendeur': vendeurs[1]
            },
            # Volkswagen Passat
            {
                'modele': Modele.objects.get(nom='Passat'),
                'prix': 24500,
                'kilometrage': 60000,
                'annee': 2019,
                'couleur': 'gris',
                'etat': 'occasion',
                'description': 'Passat diesel, confortable et spacieuse.',
                'vendeur': vendeurs[2]
            },
        ]
        
        for i, data in enumerate(voitures_data, 1):
            voiture, created = Voiture.objects.get_or_create(
                modele=data['modele'],
                annee=data['annee'],
                kilometrage=data['kilometrage'],
                defaults=data
            )
            if created:
                self.stdout.write(f"  ✓ Voiture {i}: {voiture.modele.marque.nom} {voiture.modele.nom}")
        
        self.stdout.write(self.style.SUCCESS(f'✓ {len(voitures_data)} voitures créées'))
        
        # Résumé
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('DONNÉES DE DÉMONSTRATION CRÉÉES AVEC SUCCÈS'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write('\n🎯 Comptes de test :')
        self.stdout.write('  Admin:    admin / Admin123!')
        self.stdout.write('  Vendeur:  vendeur / Vendeur123!')
        self.stdout.write('  Acheteur: acheteur / Acheteur123!')
        self.stdout.write('  Client 1: client1 / Client123!')
        self.stdout.write('  Client 2: client2 / Client123!')
        self.stdout.write('\n📊 Statistiques :')
        self.stdout.write(f'  Utilisateurs: {User.objects.count()}')
        self.stdout.write(f'  Marques: {Marque.objects.count()}')
        self.stdout.write(f'  Modèles: {Modele.objects.count()}')
        self.stdout.write(f'  Voitures: {Voiture.objects.count()}')
        self.stdout.write('\n✅ Prêt pour les tests multi-utilisateurs !')
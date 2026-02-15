import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("voitures", "0005_voiture_moderation_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="modele",
            name="annee_lancement",
            field=models.PositiveIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1900),
                    django.core.validators.MaxValueValidator(2026),
                ]
            ),
        ),
        migrations.AlterField(
            model_name="notification",
            name="type",
            field=models.CharField(
                choices=[
                    ("new_listing", "Nouvelle annonce"),
                    ("listing_moderation", "Validation annonce"),
                    ("purchase_request", "Demande d'achat"),
                    ("sale_confirmed", "Vente confirmée"),
                    ("message", "Message"),
                ],
                max_length=30,
            ),
        ),
    ]


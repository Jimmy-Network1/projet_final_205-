from django.db import migrations, models
from django.utils import timezone


def mark_existing_listings_as_approved(apps, schema_editor):
    Voiture = apps.get_model("voitures", "Voiture")
    Voiture.objects.filter(moderation_status="pending").update(
        moderation_status="approved",
        moderated_at=timezone.now(),
    )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("voitures", "0004_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="voiture",
            name="moderation_status",
            field=models.CharField(
                choices=[
                    ("pending", "En attente"),
                    ("approved", "Approuvée"),
                    ("rejected", "Refusée"),
                ],
                db_index=True,
                default="pending",
                max_length=12,
            ),
        ),
        migrations.AddField(
            model_name="voiture",
            name="moderated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(mark_existing_listings_as_approved, noop_reverse),
    ]

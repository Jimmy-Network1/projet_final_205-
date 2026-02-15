from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("voitures", "0003_merge_0002"),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("new_listing", "Nouvelle annonce"), ("purchase_request", "Demande d'achat"), ("sale_confirmed", "Vente confirmée"), ("message", "Message")], max_length=30)),
                ("titre", models.CharField(max_length=200)),
                ("contenu", models.TextField(blank=True)),
                ("url", models.CharField(blank=True, max_length=300)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("lu", models.BooleanField(default=False)),
                ("utilisateur", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to="auth.user")),
            ],
            options={
                "verbose_name": "Notification",
                "verbose_name_plural": "Notifications",
                "ordering": ["-date_creation"],
            },
        ),
    ]


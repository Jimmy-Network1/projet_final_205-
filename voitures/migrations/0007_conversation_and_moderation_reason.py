from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_conversations(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Conversation = apps.get_model("voitures", "Conversation")
    Message = apps.get_model("voitures", "Message")

    def ordered(a_id: int, b_id: int) -> tuple[int, int]:
        return (a_id, b_id) if a_id < b_id else (b_id, a_id)

    users_by_id = {u.id: u for u in User.objects.all()}

    for m in Message.objects.filter(conversation__isnull=True).iterator():
        a_id, b_id = ordered(m.expediteur_id, m.destinataire_id)
        user_a = users_by_id.get(a_id)
        user_b = users_by_id.get(b_id)
        if not user_a or not user_b:
            continue

        is_support = bool(getattr(user_a, "is_staff", False) or getattr(user_b, "is_staff", False))
        convo, _ = Conversation.objects.get_or_create(
            participant_a_id=a_id,
            participant_b_id=b_id,
            voiture_id=None,
            is_support=is_support,
        )
        Message.objects.filter(id=m.id).update(conversation_id=convo.id)


class Migration(migrations.Migration):
    dependencies = [
        ("voitures", "0006_alter_modele_annee_lancement_alter_notification_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="voiture",
            name="moderation_reason",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="voiture",
            name="moderated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="voitures_moderees",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="Conversation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_support", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "participant_a",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conversations_a",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "participant_b",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="conversations_b",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "voiture",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="conversations",
                        to="voitures.voiture",
                    ),
                ),
            ],
            options={},
        ),
        migrations.AddConstraint(
            model_name="conversation",
            constraint=models.UniqueConstraint(
                fields=("participant_a", "participant_b", "voiture", "is_support"),
                name="uniq_conversation_participants_voiture_support",
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="conversation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="messages",
                to="voitures.conversation",
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="voiture",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="voitures.voiture",
            ),
        ),
        migrations.RunPython(backfill_conversations, migrations.RunPython.noop),
    ]


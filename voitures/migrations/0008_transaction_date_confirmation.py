from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("voitures", "0007_conversation_and_moderation_reason"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="date_confirmation",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]


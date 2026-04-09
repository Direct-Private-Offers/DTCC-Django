from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="redirectevent",
            name="utm_source",
            field=models.CharField(blank=True, db_index=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="redirectevent",
            name="utm_medium",
            field=models.CharField(blank=True, db_index=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="redirectevent",
            name="utm_campaign",
            field=models.CharField(blank=True, db_index=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="redirectevent",
            name="utm_term",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="redirectevent",
            name="utm_content",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="redirectevent",
            name="gclid",
            field=models.CharField(blank=True, db_index=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="redirectevent",
            name="fbclid",
            field=models.CharField(blank=True, db_index=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="redirectevent",
            name="msclkid",
            field=models.CharField(blank=True, db_index=True, max_length=128, null=True),
        ),
    ]

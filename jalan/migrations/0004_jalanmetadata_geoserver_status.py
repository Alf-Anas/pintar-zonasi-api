# Generated by Django 5.1.3 on 2024-12-04 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jalan", "0003_jalanmetadata_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="jalanmetadata",
            name="geoserver_status",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]

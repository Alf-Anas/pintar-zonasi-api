# Generated by Django 5.1.3 on 2024-12-06 20:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jalan", "0006_rename_status_jalanmetadata_data_status_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="jalan",
            name="cost",
            field=models.DecimalField(
                blank=True, decimal_places=8, default=0, max_digits=15, null=True
            ),
        ),
    ]

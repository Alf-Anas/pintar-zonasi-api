# Generated by Django 5.1.3 on 2024-12-04 13:11

import django.contrib.gis.db.models.fields
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="JalanMetadata",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                ("road_table", models.CharField(max_length=50, unique=True)),
                ("description", models.CharField(max_length=255)),
                (
                    "bbox",
                    django.contrib.gis.db.models.fields.PolygonField(
                        blank=True, null=True, srid=4326
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "tb_jalan_metadata",
            },
        ),
        migrations.CreateModel(
            name="Jalan",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("osm_id", models.CharField(blank=True, default="", max_length=255)),
                ("name", models.CharField(blank=True, default="", max_length=255)),
                ("fclass", models.CharField(blank=True, default="", max_length=255)),
                ("source", models.IntegerField(blank=True, default=0)),
                ("target", models.IntegerField(blank=True, default=0)),
                (
                    "cost",
                    models.DecimalField(
                        blank=True, decimal_places=6, default=0, max_digits=10
                    ),
                ),
                ("properties", models.JSONField()),
                (
                    "mline",
                    django.contrib.gis.db.models.fields.MultiLineStringField(srid=4326),
                ),
                (
                    "file_metadata",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="jalan",
                        to="jalan.jalanmetadata",
                    ),
                ),
            ],
            options={
                "db_table": "tb_jalan",
            },
        ),
    ]

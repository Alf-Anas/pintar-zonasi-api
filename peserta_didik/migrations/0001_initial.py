# Generated by Django 5.1.3 on 2024-12-03 16:59

import django.contrib.gis.db.models.fields
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PesertaDidikMetadata",
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
                ("level", models.CharField(max_length=50)),
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
                "db_table": "tb_peserta_didik_metadata",
            },
        ),
        migrations.CreateModel(
            name="PesertaDidik",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("nisn", models.CharField(blank=True, default="", max_length=50)),
                ("nama", models.CharField(blank=True, default="", max_length=255)),
                (
                    "jenis_kelamin",
                    models.CharField(blank=True, default="", max_length=50),
                ),
                (
                    "tanggal_lahir",
                    models.DateField(blank=True, default=None, null=True),
                ),
                ("alamat", models.CharField(blank=True, default="", max_length=255)),
                ("prioritas", models.IntegerField(blank=True, default=0)),
                (
                    "keterangan",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("lat", models.FloatField(blank=True, null=True)),
                ("lon", models.FloatField(blank=True, null=True)),
                ("point", django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "file_metadata",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="peserta_didik",
                        to="peserta_didik.pesertadidikmetadata",
                    ),
                ),
            ],
            options={
                "db_table": "tb_peserta_didik",
            },
        ),
    ]

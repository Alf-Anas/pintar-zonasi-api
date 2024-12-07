from django.contrib.gis.db import models
import uuid
import random
import string


class JalanMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    road_table = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255)
    bbox = models.PolygonField(null=True, blank=True)
    data_status = models.CharField(
        max_length=50, null=True, blank=True
    )  # UPLOADED | DEPLOYING | DEPLOYED | FAILED
    geoserver_status = models.CharField(
        max_length=50, null=True, blank=True
    )  # DEPLOYED | FAILED
    topology_status = models.CharField(
        max_length=50, null=True, blank=True
    )  # CREATING | CREATED | FAILED

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tb_jalan_metadata"

    def save(self, *args, **kwargs):
        if not self.road_table:  # Only generate if the field is empty
            while True:
                # Generate a unique table name with 4 lowercase alphabetic characters
                random_suffix = "".join(random.choices(string.ascii_lowercase, k=4))
                table_name = f"tb_jalan_x_{random_suffix}"

                # Check if the table name already exists
                if not JalanMetadata.objects.filter(road_table=table_name).exists():
                    self.road_table = table_name
                    break

        super().save(*args, **kwargs)


class Jalan(models.Model):
    id = models.AutoField(primary_key=True)
    file_metadata = models.ForeignKey(
        JalanMetadata, related_name="jalan", on_delete=models.CASCADE
    )
    # For pgrouting
    source = models.IntegerField(blank=True, null=True, default=0)
    target = models.IntegerField(blank=True, null=True, default=0)
    cost = models.DecimalField(
        blank=True, null=True, default=0, max_digits=15, decimal_places=8
    )
    reverse_cost = models.DecimalField(
        blank=True, null=True, default=0, max_digits=15, decimal_places=8
    )
    # properties to save all fields
    properties = models.JSONField()
    # GeoDjango-specific: a geometry field (LineStringField)
    mline = models.LineStringField()

    # Returns the string representation of the model.
    def __str__(self):
        return f"{self.file_metadata.name} - {self.id}"

    class Meta:
        db_table = "tb_jalan"

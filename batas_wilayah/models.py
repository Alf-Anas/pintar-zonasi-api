from django.contrib.gis.db import models
import uuid


class BatasWilayahMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    description = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tb_batas_wilayah_metadata"


class BatasWilayah(models.Model):
    id = models.AutoField(primary_key=True)
    file_metadata = models.ForeignKey(
        BatasWilayahMetadata, related_name="batas_wilayah", on_delete=models.CASCADE
    )
    # properties to save all fields
    properties = models.JSONField()
    # GeoDjango-specific: a geometry field (MultiPolygonField)
    mpoly = models.MultiPolygonField()

    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Returns the string representation of the model.
    def __str__(self):
        return f"{self.file_metadata.name} - {self.id}"

    class Meta:
        db_table = "tb_batas_wilayah"

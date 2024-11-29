from django.contrib.gis.db import models
import uuid


class SekolahMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    level = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    bbox = models.PolygonField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tb_sekolah_metadata"


class Sekolah(models.Model):
    id = models.AutoField(primary_key=True)
    file_metadata = models.ForeignKey(
        SekolahMetadata, related_name="sekolah", on_delete=models.CASCADE
    )
    tipe = models.CharField(max_length=50, blank=True, default="")
    npsn = models.CharField(max_length=50, blank=True, default="")
    nama = models.CharField(max_length=255, blank=True, default="")
    alamat = models.CharField(max_length=255, blank=True, default="")
    kuota = models.IntegerField(blank=True, default=0)
    keterangan = models.CharField(max_length=255, blank=True, default="")
    lat = models.FloatField(null=True, blank=True)
    lon = models.FloatField(null=True, blank=True)

    # GeoDjango-specific: a geometry field (Point)
    point = models.PointField()

    # Timestamp fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Returns the string representation of the model.
    def __str__(self):
        return f"{self.file_metadata.name} - {self.id}"

    def save(self, *args, **kwargs):
        if self.lat is not None:
            self.lat = round(self.lat, 6)
        if self.lon is not None:
            self.lon = round(self.lon, 6)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "tb_sekolah"

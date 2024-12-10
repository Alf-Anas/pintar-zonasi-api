from django.contrib.gis.db import models
import uuid


class ProjectMetadata(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    level = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    layers = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=50)  # DRAFT | PUBLISHED
    bbox = models.PolygonField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "tb_project_metadata"

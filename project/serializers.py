from rest_framework import serializers
from .models import ProjectMetadata


class ProjectMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMetadata
        fields = (
            "id",
            "name",
            "level",
            "type",
            "description",
            "layers",
            "status",
            "bbox",
            "created_at",
            "updated_at",
        )

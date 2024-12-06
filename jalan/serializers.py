from rest_framework import serializers
from .models import JalanMetadata


class JalanMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = JalanMetadata
        fields = (
            "id",
            "name",
            "road_table",
            "description",
            "bbox",
            "data_status",
            "geoserver_status",
            "topology_status",
            "created_at",
            "updated_at",
        )

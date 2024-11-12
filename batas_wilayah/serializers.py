from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework import serializers
from .models import BatasWilayah, BatasWilayahMetadata


class BatasWilayahMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatasWilayahMetadata
        fields = (
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
        )


class BatasWilayahDetailSerializer(serializers.ModelSerializer):
    file_metadata = (
        BatasWilayahMetadataSerializer()
    )  # Nested serializer for file metadata

    id = serializers.IntegerField()

    class Meta:
        model = BatasWilayah
        fields = (
            "id",
            "file_metadata",  # Include metadata in the response
            "properties",
            "mpoly",
        )
        geo_field = "mpoly"

    def to_representation(self, instance):
        # Get the default representation
        representation = super().to_representation(instance)

        # Create the GeoJSON structure
        geojson_representation = {
            "type": "Feature",  # GeoJSON type (Feature)
            "geometry": representation.pop("mpoly"),  # Pop and insert geometry
            "properties": representation.pop("properties"),  # Pop and insert properties
        }

        # Replace the original geometry with the geojson field
        representation["geojson"] = geojson_representation

        return representation

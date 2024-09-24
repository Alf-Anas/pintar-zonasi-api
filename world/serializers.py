from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import WorldBorder


class WorldBorderSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = WorldBorder
        fields = (
            "name",
            "area",
            "pop2005",
            "mpoly",
        )  # Include spatial fields like mpoly
        geo_field = "mpoly"

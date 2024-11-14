import geopandas as gpd
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.contrib.gis.geos import GEOSGeometry
from shapely.geometry import MultiPolygon
from .models import BatasWilayah, BatasWilayahMetadata
from .serializers import BatasWilayahDetailSerializer, BatasWilayahMetadataSerializer
from geodjango.utils import (
    is_valid_geospatial_file,
    find_shapefile_path,
    extract_zip_to_temp,
)
from shapely.wkb import dumps, loads


class BatasWilayahMetadataList(generics.ListAPIView):
    queryset = BatasWilayahMetadata.objects.all().order_by("created_at")
    serializer_class = BatasWilayahMetadataSerializer


class BatasWilayahMetadataDelete(generics.DestroyAPIView):
    queryset = BatasWilayahMetadata.objects.all()
    serializer_class = BatasWilayahMetadataSerializer


class BatasWilayahMetadataDetail(generics.RetrieveAPIView):
    queryset = BatasWilayahMetadata.objects.all()
    serializer_class = BatasWilayahMetadataSerializer


class BatasWilayahListByMetadataId(generics.ListAPIView):
    serializer_class = BatasWilayahDetailSerializer

    def get_queryset(self):
        # Filter BatasWilayah by file_id from the URL
        metadata_id = self.kwargs.get("metadata_id")
        return BatasWilayah.objects.filter(file_metadata__id=metadata_id)


class BatasWilayahDetail(generics.RetrieveAPIView):
    queryset = BatasWilayah.objects.all()
    serializer_class = BatasWilayahDetailSerializer


class BatasWilayahUpload(generics.CreateAPIView):
    """
    API view to upload a geospatial file and metadata.
    Supported formats: GeoJSON, KML, or Shapefile (in zip format).
    """

    def post(self, request, *args, **kwargs):
        # Get the uploaded file and metadata
        name = request.data.get("name")
        description = request.data.get("description")
        file = request.FILES.get("file")

        if not name:
            return Response(
                {"error": "Name is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not file:
            return Response(
                {"error": "File is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if the file is valid and determine the format
        file_format = is_valid_geospatial_file(file)

        if not file_format:
            return Response(
                {
                    "error": "Invalid file format. Supported formats: .zip, .kml, .geojson"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Process the file based on its format
        try:
            # Save metadata (name, description) to the BatasWilayahMetadata model
            metadata = BatasWilayahMetadata.objects.create(
                name=name, description=description
            )

            if file_format == "zip":
                # Handle shapefile in zip format
                temp_dir = extract_zip_to_temp(file)
                shapefile_path = find_shapefile_path(temp_dir)

                # Process the shapefile (e.g., load into GeoDjango models)
                self.process_file(shapefile_path, metadata)

            elif file_format == "kml":
                # Process KML file (e.g., parse and load into GeoDjango)
                self.process_file(file, metadata)

            elif file_format == "geojson":
                # Process GeoJSON file (e.g., parse and load into GeoDjango)
                self.process_file(file, metadata)

            return Response(
                {"message": "File uploaded successfully", "metadata_id": metadata.id},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def process_file(self, file_path, metadata: BatasWilayahMetadata):
        """
        Process the extracted file and load data into the BatasWilayah model.
        """
        gdf = gpd.read_file(file_path)

        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        total_bbox = gdf.total_bounds
        metadata.bbox = Polygon.from_bbox(total_bbox)
        metadata.save()

        for _, row in gdf.iterrows():

            geom = row["geometry"]
            if geom.geom_type == "Polygon":
                geom = MultiPolygon([geom])
            elif geom.geom_type != "MultiPolygon":
                # Skip non-Polygon and non-MultiPolygon geometries
                return

            geom_2d = loads(dumps(geom, output_dimension=2))
            geos_geom = GEOSGeometry(geom_2d.wkt)
            # Extract the properties (attribute data)
            properties = row.drop("geometry").to_dict()

            # Save each feature to the BatasWilayah model
            BatasWilayah.objects.create(
                file_metadata=metadata, properties=properties, mpoly=geos_geom
            )

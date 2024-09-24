import os
import zipfile
import tempfile
import geopandas as gpd
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.gis.geos import MultiPolygon
from django.contrib.gis.geos import GEOSGeometry
from shapely.geometry import MultiPolygon
from .models import WorldBorder
from .serializers import WorldBorderSerializer


class WorldBorderList(generics.ListCreateAPIView):
    queryset = WorldBorder.objects.all()
    serializer_class = WorldBorderSerializer


class WorldBorderDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = WorldBorder.objects.all()
    serializer_class = WorldBorderSerializer


class WorldBorderUpload(generics.CreateAPIView):
    queryset = WorldBorder.objects.all()
    serializer_class = WorldBorderSerializer

    def post(self, request, *args, **kwargs):
        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        file = request.FILES["file"]

        # Create a temporary directory to extract the zip file
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, file.name)
            with open(zip_path, "wb") as temp_file:
                for chunk in file.chunks():
                    temp_file.write(chunk)

            # Extract the zip file
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

            # Read the shapefile with GeoPandas
            shapefile_path = os.path.join(
                temp_dir,
                [name for name in os.listdir(temp_dir) if name.endswith(".shp")][0],
            )
            gdf = gpd.read_file(shapefile_path)

            if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)

            # Filter columns
            gdf_filtered = gdf[
                [
                    "FIPS",
                    "ISO2",
                    "ISO3",
                    "UN",
                    "NAME",
                    "AREA",
                    "POP2005",
                    "REGION",
                    "SUBREGION",
                    "LON",
                    "LAT",
                    "geometry",
                ]
            ]

            # Save to the database
            for _, row in gdf_filtered.iterrows():

                geom = row["geometry"]
                if geom.geom_type == "Polygon":
                    geom = MultiPolygon([geom])

                # Convert Shapely MultiPolygon to GEOSGeometry
                geos_geom = GEOSGeometry(geom.wkt)

                instance = WorldBorder(
                    name=row["NAME"],
                    area=row["AREA"],
                    pop2005=row["POP2005"],
                    fips=row["FIPS"],
                    iso2=row["ISO2"],
                    iso3=row["ISO3"],
                    un=row["UN"],
                    region=row["REGION"],
                    subregion=row["SUBREGION"],
                    lon=geom.centroid.x,
                    lat=geom.centroid.y,
                    mpoly=geos_geom,
                )
                instance.save()

        return Response(
            {"message": "Shapefile uploaded and processed."},
            status=status.HTTP_201_CREATED,
        )

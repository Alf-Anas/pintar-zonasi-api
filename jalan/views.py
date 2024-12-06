import geopandas as gpd
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.gis.geos import Polygon
from .models import JalanMetadata
from threading import Thread
from .serializers import JalanMetadataSerializer
from geodjango.utils import (
    is_valid_geospatial_file,
    find_shapefile_path,
    extract_zip_to_temp,
    create_geoserver_layer,
    delete_geoserver_layer,
)
from shapely.wkb import dumps, loads
from django.db import connection
import json


class JalanMetadataList(generics.ListAPIView):
    queryset = JalanMetadata.objects.all().order_by("created_at")
    serializer_class = JalanMetadataSerializer


class JalanMetadataDelete(generics.DestroyAPIView):
    queryset = JalanMetadata.objects.all()
    serializer_class = JalanMetadataSerializer

    def delete(self, request, *args, **kwargs):
        # Retrieve the metadata object
        metadata = self.get_object()

        # Get the table name
        road_table = metadata.road_table
        msg = ""

        # Attempt to drop the table if it exists
        try:
            if road_table:
                road_table_verticles = f"{road_table}_vertices_pgr"
                with connection.cursor() as cursor:
                    cursor.execute(f"DROP TABLE IF EXISTS {road_table};")
                    cursor.execute(f"DROP TABLE IF EXISTS {road_table_verticles};")
                msg = f"Table {road_table} dropped successfully."
                delete_geoserver_layer(road_table)
            else:
                msg = "No associated road_table to drop."
        except Exception as e:
            return Response(
                {"error": f"Failed to drop table {road_table}: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Proceed to delete the metadata
        super().delete(request, *args, **kwargs)
        return Response(
            {"message": f"Metadata deleted successfully, {msg}"},
            status=status.HTTP_200_OK,
        )


class JalanMetadataDetail(generics.RetrieveAPIView):
    queryset = JalanMetadata.objects.all()
    serializer_class = JalanMetadataSerializer


class JalanUpload(generics.CreateAPIView):
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
            # Save metadata (name, description) to the JalanMetadata model
            metadata = JalanMetadata.objects.create(
                name=name, description=description, data_status="UPLOADED"
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

    def process_file(self, file_path, metadata: JalanMetadata):
        """
        Process the extracted file and load data into the Jalan model.
        """
        gdf = gpd.read_file(file_path)

        if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
            gdf = gdf.to_crs(epsg=4326)

        total_bbox = gdf.total_bounds
        metadata.bbox = Polygon.from_bbox(total_bbox)
        metadata.save()

        table_name = metadata.road_table
        self.duplicate_tb_jalan_structure(table_name)

        # Start the background thread
        thread = Thread(target=self.iterate_and_save, args=(gdf, table_name, metadata))
        thread.start()

    def iterate_and_save(self, gdf, table_name, metadata: JalanMetadata):
        """
        Iterate and save road in new created table
        """
        metadata.data_status = "DEPLOYING"
        metadata.save()

        try:
            for _, row in gdf.iterrows():

                geom = row["geometry"]
                if (
                    geom.geom_type != "LineString"
                    and geom.geom_type != "MultiLineString"
                ):
                    continue

                geom_2d = loads(dumps(geom, output_dimension=2))
                geom_wkt = geom_2d.wkt

                properties = row.drop("geometry").to_dict()

                # Insert data into the created table
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"""
                        INSERT INTO {table_name} (mline, properties, file_metadata_id)
                        VALUES (ST_GeomFromText(%s, 4326), %s, %s)
                    """,
                        [
                            geom_wkt,
                            json.dumps(properties),
                            metadata.id,
                        ],
                    )

            metadata.data_status = "DEPLOYED"
            metadata.save()

            geo_layer = create_geoserver_layer(table_name, table_name)
            if geo_layer["success"]:
                metadata.geoserver_status = "DEPLOYED"
            else:
                metadata.geoserver_status = "FAILED"
            metadata.save()

        except Exception as e:
            metadata.data_status = "FAILED"
            metadata.save()
            print(str(e))

    def duplicate_tb_jalan_structure(self, table_name):
        with connection.cursor() as cursor:
            # Copy the structure of tb_jalan without data
            cursor.execute(
                f"""
                CREATE TABLE {table_name} (LIKE tb_jalan INCLUDING ALL);
            """
            )
            # Create indexes on the new table
            cursor.execute(
                f"""
                CREATE INDEX idx_source_{table_name} ON {table_name}(source);
                """
            )
            cursor.execute(
                f"""
                CREATE INDEX idx_target_{table_name} ON {table_name}(target);
                """
            )
            cursor.execute(
                f"""
                CREATE INDEX idx_cost_{table_name} ON {table_name}(cost);
                """
            )
            cursor.execute(
                f"""
                CREATE INDEX idx_mline_{table_name} ON {table_name} USING GIST(mline);
                """
            )


class JalanGenerateTopology(generics.RetrieveAPIView):
    """
    API view to generate topology based on id
    """

    def put(self, request, *args, **kwargs):
        metadata_id = kwargs.get("pk")

        try:
            metadata = JalanMetadata.objects.get(id=metadata_id)
            metadata.topology_status = "CREATING"
            metadata.save()

            road_table = metadata.road_table
            # Create topology 0.0001 deg = 11.1 m
            create_topology_query = f"""
                SELECT pgr_createTopology('{road_table}', 0.0001, 'mline', 'id');
            """

            pace = 15  # 15 minutes/km
            speed = (1 * 1000) / (pace * 60)  # format it in m/s

            # Update the cost column with the calculated values, Assuming 15 minutes per kilometer
            update_cost_query = f"""
                UPDATE {road_table}
                SET cost = (ST_Length(ST_Transform(mline, 3857)) / {speed}) / 60;
            """

            # Check if source, target, and cost columns are populated
            check_query = f"""
                SELECT id, source, target, cost
                FROM {road_table}
                WHERE source IS NOT NULL AND target IS NOT NULL AND cost > 0
                ORDER BY RANDOM()
                LIMIT 10;
            """

            with connection.cursor() as cursor:
                cursor.execute(create_topology_query)
                cursor.execute(update_cost_query)

                # Check random rows for validity
                cursor.execute(check_query)
                results = cursor.fetchall()

            if len(results) == 10:
                metadata.topology_status = "CREATED"
                metadata.save()
                return Response(
                    {"message": "Topology created successfully", "layer": road_table},
                    status=status.HTTP_201_CREATED,
                )
            else:
                metadata.topology_status = "FAILED"
                metadata.save()
                raise ValueError(
                    f"Failed to create topology, the results validity length only {len(results)}"
                )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

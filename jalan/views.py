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
    create_concave_hull,
    geojson_line_length,
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

                geo_row = row["geometry"]
                # If the geometry is not a LineString or MultiLineString, skip
                if geo_row.geom_type == "LineString":
                    geometries = [geo_row]
                elif geo_row.geom_type == "MultiLineString":
                    # If it's a MultiLineString, break it into individual LineStrings
                    geometries = [
                        line for line in geo_row
                    ]  # This will be a list of LineString objects
                else:
                    # Skip if it's not a valid geometry type
                    continue

                for geom in geometries:
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
                CREATE INDEX idx_reverse_cost_{table_name} ON {table_name}(reverse_cost);
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
                SELECT pgr_createTopology('{road_table}', 0.00005, 'mline', 'id');
            """

            pace = 15  # 15 minutes/km
            speed = (1 * 1000) / (pace * 60)  # format it in m/s

            # Update the cost column with the calculated values, Assuming 15 minutes per kilometer
            update_cost_query = f"""
                UPDATE {road_table}
                SET cost = (ST_Length(ST_Transform(mline, 3857)) / {speed}) / 60,
                    reverse_cost = (ST_Length(ST_Transform(mline, 3857)) / {speed}) / 60;
            """

            # Check if source, target, and cost columns are populated
            check_query = f"""
                SELECT id, source, target, cost, reverse_cost
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


class JalanFindRoute(generics.RetrieveAPIView):
    """
    API view to get routing
    """

    def get(self, request, *args, **kwargs):
        metadata_id = kwargs.get("pk")
        # Get query parameters from the request
        start_lat = request.query_params.get("start-lat")
        start_lon = request.query_params.get("start-lon")
        end_lat = request.query_params.get("end-lat")
        end_lon = request.query_params.get("end-lon")

        # Check if the parameters are provided
        if start_lat is None or start_lon is None or end_lat is None or end_lon is None:
            return Response(
                {
                    "error": "Both start and end 'lon' and 'lat' query parameters are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_lat = float(start_lat)
            start_lon = float(start_lon)
            end_lat = float(end_lat)
            end_lon = float(end_lon)
        except ValueError:
            return Response(
                {"error": "'lon' and 'lat' must be valid numeric values."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            metadata = JalanMetadata.objects.get(id=metadata_id)
            road_table = metadata.road_table
            vertices_table = f"{road_table}_vertices_pgr"
            # Find Routing
            routing_query = f"""
                WITH
                    start_node AS (
                        SELECT id
                        FROM {vertices_table}
                        ORDER BY the_geom <-> ST_SetSRID(ST_Point({start_lon}, {start_lat}), 4326)
                        LIMIT 1
                    ),
                    end_node AS (
                        SELECT id
                        FROM {vertices_table}
                        ORDER BY the_geom <-> ST_SetSRID(ST_Point({end_lon}, {end_lat}), 4326)
                        LIMIT 1
                    ),
                    path AS (
                        SELECT * 
                        FROM pgr_dijkstra(
                            'SELECT id, source, target, cost, reverse_cost FROM {road_table}',
                            (SELECT id FROM start_node),
                            (SELECT id FROM end_node),
                            directed := false
                        )
                    ),
                    list AS (
                        SELECT p.*, e.mline
                            FROM path p
                            JOIN {road_table} e ON e.id = p.edge
                            ORDER BY p.seq
                    )

                SELECT ST_AsGeoJSON(ST_LineMerge(ST_Union(mline))) AS geojson from list		
            """

            with connection.cursor() as cursor:
                cursor.execute(routing_query)
                result = cursor.fetchone()

            if result and result[0]:
                geometry = json.loads(result[0])
                geo_length = geojson_line_length(geometry)
                res_features = {
                    "type": "Feature",
                    "properties": {
                        "start_lat": start_lat,
                        "start_lon": start_lon,
                        "end_lat": end_lat,
                        "end_lon": end_lon,
                        "name": "Route",
                        "length": geo_length,
                        "time": round(15 * geo_length, 1),
                    },
                    "geometry": geometry,
                }
                return Response(
                    {
                        "type": "FeatureCollection",
                        "features": [res_features],
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                raise ValueError(
                    f"Failed to find route from the given coordinate and time"
                )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JalanFindIsochrone(generics.RetrieveAPIView):
    """
    API view to get isochrone
    """

    def get(self, request, *args, **kwargs):
        metadata_id = kwargs.get("pk")
        # Get query parameters from the request
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        time = request.query_params.get("time")
        filter = request.query_params.get("filter", "isochrone|buffer|point")

        # Check if the parameters are provided
        if lat is None or lon is None or time is None:
            return Response(
                {
                    "error": "Both 'lon' and 'lat' and time query parameters are required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            metadata = JalanMetadata.objects.get(id=metadata_id)
            road_table = metadata.road_table
            vertices_table = f"{road_table}_vertices_pgr"
            # Find nearest node
            find_node = f"""
                SELECT ST_AsGeoJSON(the_geom) AS geojson
                        FROM {vertices_table}
                        ORDER BY the_geom <-> ST_SetSRID(ST_Point({lon}, {lat}), 4326)
                        LIMIT 5;
            """

            # Create isochrone query
            create_isochrone = f"""
                WITH
                    start_node AS (
                        SELECT id
                        FROM {vertices_table}
                        ORDER BY the_geom <-> ST_SetSRID(ST_Point({lon}, {lat}), 4326)
                        LIMIT 1
                    )

                SELECT ST_AsGeoJSON(isochrone_polygon) AS geojson
                FROM (
                    SELECT ST_Buffer(merged_lines, 0.0002) AS isochrone_polygon
                        FROM (
                            SELECT ST_Union(w.mline) AS merged_lines
                            FROM pgr_drivingDistance(
                                'SELECT id, source, target, cost, reverse_cost FROM {road_table}',
                                (SELECT id FROM start_node),
                               {time}
                            ) AS r
                            JOIN {road_table} AS w ON r.edge = w.id
                        ) AS subquery
                ) AS final_result;
            """

            with connection.cursor() as cursor:
                cursor.execute(find_node)
                out_point = cursor.fetchall()
                cursor.execute(create_isochrone)
                result = cursor.fetchone()

            if result and result[0]:
                geojson_buffer = json.loads(result[0])
                concave_geojson = create_concave_hull(geojson_buffer, 0.003, 50)

                res_concave = {
                    "type": "Feature",
                    "properties": {
                        "lat": lat,
                        "lon": lon,
                        "time": time,
                        "name": "Concave",
                    },
                    "geometry": json.loads(concave_geojson),
                }
                res_buffer = {
                    "type": "Feature",
                    "properties": {
                        "lat": lat,
                        "lon": lon,
                        "time": time,
                        "name": "Iso Buffer",
                    },
                    "geometry": geojson_buffer,
                }
                res_point = [
                    {
                        "type": "Feature",
                        "properties": {"name": "PT", "idx": idx},
                        "geometry": json.loads(row[0]),
                    }
                    for idx, row in enumerate(out_point)
                ]
                res_features = []
                if "isochrone" in filter:
                    res_features.append(res_concave)
                if "buffer" in filter:
                    res_features.append(res_buffer)
                if "point" in filter:
                    res_features.extend(res_point)

                return Response(
                    {
                        "type": "FeatureCollection",
                        "features": res_features,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                raise ValueError(
                    f"Failed to create isochrone from the given coordinate and time"
                )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

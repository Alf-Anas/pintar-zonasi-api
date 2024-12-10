from rest_framework import generics, status
from rest_framework.response import Response
from .models import ProjectMetadata
from .serializers import (
    ProjectMetadataSerializer,
)
from jalan.models import JalanMetadata
from sekolah.models import SekolahMetadata, Sekolah
from geodjango.utils import (
    create_concave_hull,
    geojson_line_length,
    add_unique_items,
    calculate_distance,
)
from django.db import connection
import json
from django.contrib.gis.geos import GEOSGeometry


class ProjectMetadataList(generics.ListAPIView):
    queryset = ProjectMetadata.objects.all().order_by("-created_at")
    serializer_class = ProjectMetadataSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        project_type = self.request.query_params.get("type")
        if project_type:  # Check if the 'type' parameter is provided
            queryset = queryset.filter(type=project_type)
        return queryset


class ProjectMetadataDelete(generics.DestroyAPIView):
    queryset = ProjectMetadata.objects.all()
    serializer_class = ProjectMetadataSerializer


class ProjectMetadataDetail(generics.RetrieveAPIView):
    queryset = ProjectMetadata.objects.all()
    serializer_class = ProjectMetadataSerializer


class ProjectCreate(generics.CreateAPIView):
    """
    API view to create project
    """

    def post(self, request, *args, **kwargs):
        name = request.data.get("name")
        level = request.data.get("level")
        type = request.data.get("type")
        description = request.data.get("description")

        if not name:
            return Response(
                {"error": "Name is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not level:
            return Response(
                {"error": "Level is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not type:
            return Response(
                {"error": "Type is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            metadata = ProjectMetadata.objects.create(
                name=name,
                level=level,
                type=type,
                description=description,
                status="DRAFT",
            )

            return Response(
                {"message": "Project created successfully", "metadata_id": metadata.id},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectSaveLayer(generics.RetrieveAPIView):
    """
    API view to save layers
    """

    def put(self, request, *args, **kwargs):
        metadata_id = kwargs.get("pk")

        try:
            metadata = ProjectMetadata.objects.get(id=metadata_id)
            layers = request.data.get("layers")

            if layers is not None:
                # Find the layer where type is "jalan"
                jalan_layer = next(
                    (layer for layer in layers if layer["type"] == "jalan"), None
                )
                if jalan_layer:
                    jalan_id = jalan_layer["id"]
                    jalan_metadata = JalanMetadata.objects.get(id=jalan_id)
                    if jalan_metadata:
                        metadata.bbox = jalan_metadata.bbox
                # Update the 'layers' field in the metadata
                metadata.layers = layers
                metadata.save()

                return Response(
                    {"message": "Layer updated successfully."},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": "Layers data is missing."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectUpdateStatus(generics.RetrieveAPIView):
    """
    API view to update status
    """

    def put(self, request, *args, **kwargs):
        metadata_id = kwargs.get("pk")
        in_status = kwargs.get("status")

        if in_status != "DRAFT" and in_status != "PUBLISHED":
            return Response(
                {"error": "Status invalid!."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            metadata = ProjectMetadata.objects.get(id=metadata_id)
            metadata.status = in_status
            metadata.save()

            return Response(
                {"message": "Status updated successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProjectListZonasi(generics.ListAPIView):
    queryset = ProjectMetadata.objects.all().order_by("-created_at")
    serializer_class = ProjectMetadataSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        project_level = self.request.query_params.get("level")

        if project_level:
            queryset = queryset.filter(level=project_level, status="PUBLISHED")
        else:
            queryset = queryset.filter(status="PUBLISHED")
        return queryset


class ProjectFindZonasi(generics.RetrieveAPIView):
    """
    API view to get zonasi based on lat lon query
    """

    def get(self, request, *args, **kwargs):
        metadata_id = kwargs.get("pk")
        # Get query parameters from the request
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        min_time = 5
        max_time = 60

        # Check if the parameters are provided
        if lat is None or lon is None:
            return Response(
                {"error": "Both 'lon' and 'lat' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            metadata = ProjectMetadata.objects.get(id=metadata_id)
            layers = metadata.layers
            jalan = None
            sekolah = []

            # Loop through layers
            for layer in layers:
                if layer["type"] == "jalan" and jalan is None:
                    jalan = layer  # Assign the first "jalan" layer
                if layer["type"] == "sekolah":
                    sekolah.append(layer)  # Add "sekolah" layers to the list

            if jalan is None:
                raise ValueError(f"Jalan Layer is not found!")
            jalan_metadata = JalanMetadata.objects.get(id=jalan["id"])

            if not sekolah:
                raise ValueError("Sekolah Layers are not found!")
            sekolah_metadata = []
            for sekolah_layer in sekolah:
                metadata = SekolahMetadata.objects.get(id=sekolah_layer["id"])
                sekolah_metadata.append(metadata)

            road_table = jalan_metadata.road_table
            vertices_table = f"{road_table}_vertices_pgr"
            res_isochrone = []
            res_sekolah = {"zonasi": [], "non_zonasi": []}
            for time in range(min_time, max_time + 1, 5):
                res = self.generate_isochrone(
                    road_table=road_table,
                    vertices_table=vertices_table,
                    lon=lon,
                    lat=lat,
                    time=time,
                    list_sekolah_metadata=sekolah_metadata,
                )
                res_isochrone.append(res["isochrone"])
                add_unique_items(res_sekolah["zonasi"], res["sekolah"]["zonasi"])
                add_unique_items(
                    res_sekolah["non_zonasi"], res["sekolah"]["non_zonasi"]
                )
                if len(res_sekolah["zonasi"]) > 3:
                    break

            res_route = []
            for sekolah in res_sekolah["zonasi"]:
                route = self.zonasi_sekolah_route(
                    road_table, vertices_table, lon, lat, sekolah
                )
                if route:
                    res_route.append(route)

            return Response(
                {
                    "sekolah": res_sekolah,
                    "isochrone": {
                        "type": "FeatureCollection",
                        "features": res_isochrone,
                    },
                    "route": {
                        "type": "FeatureCollection",
                        "features": res_route,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def generate_isochrone(
        self,
        road_table: str,
        vertices_table: str,
        lon,
        lat,
        time: int,
        list_sekolah_metadata: list[SekolahMetadata],
    ):
        """
        Process the isochrone
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
            cursor.execute(create_isochrone)
            result = cursor.fetchone()

        if result and result[0]:
            geojson_buffer = json.loads(result[0])
            concave_geojson = create_concave_hull(geojson_buffer, 0.003, 20)

            res_concave = {
                "type": "Feature",
                "properties": {
                    "lat": lat,
                    "lon": lon,
                    "time": time,
                    "name": f"±{time} Menit",
                },
                "geometry": json.loads(concave_geojson),
            }

            str_geom = str(res_concave["geometry"])

            res_sekolah = {"zonasi": [], "non_zonasi": []}

            for sekolah_metadata in list_sekolah_metadata:
                list_sekolah = self.find_sekolah(str_geom, sekolah_metadata, time)

                if sekolah_metadata.zonasi:
                    res_sekolah["zonasi"].extend(list_sekolah)
                else:
                    res_sekolah["non_zonasi"].extend(list_sekolah)

            return {"isochrone": res_concave, "sekolah": res_sekolah}
        else:
            raise ValueError(
                f"Failed to create isochrone from the given coordinate {lat}, {lon} and time {time}"
            )

    def find_sekolah(
        self, str_geometry: str, sekolah_metadata: SekolahMetadata, time: int
    ):
        """
        Find sekolah inside isochrone
        """

        # Convert GeoJSON to GEOSGeometry
        polygon_geom = GEOSGeometry(str_geometry, srid=4326)

        # Filter sekolah points within the polygon
        sekolah_inside_polygon = Sekolah.objects.filter(
            point__within=polygon_geom, file_metadata_id=sekolah_metadata.id
        )

        # Dynamically get field names of the Sekolah model
        exclude_fields = {"created_at", "updated_at", "file_metadata", "point"}
        include_fields = [
            field.name
            for field in Sekolah._meta.get_fields()
            if field.name not in exclude_fields
        ]

        sekolah_with_time = [
            {**item, "time": time}
            for item in sekolah_inside_polygon.values(*include_fields)
        ]

        return sekolah_with_time

    def zonasi_sekolah_route(
        self,
        road_table: str,
        vertices_table: str,
        lon,
        lat,
        sekolah: Sekolah,
    ):
        """
        Find sekolah inside isochrone
        """

        # Find Routing
        routing_query = f"""
            WITH
                start_node AS (
                    SELECT id
                    FROM {vertices_table}
                    ORDER BY the_geom <-> ST_SetSRID(ST_Point({lon}, {lat}), 4326)
                    LIMIT 1
                ),
                end_node AS (
                    SELECT id
                    FROM {vertices_table}
                    ORDER BY the_geom <-> ST_SetSRID(ST_Point({sekolah["lon"]}, {sekolah["lat"]}), 4326)
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
            radius = calculate_distance(lat, lon, sekolah["lat"], sekolah["lon"])
            sekolah["radius"] = radius
            sekolah["route"] = geo_length

            res_features = {
                "type": "Feature",
                "properties": {
                    "start_lat": lat,
                    "start_lon": lon,
                    "end_lat": sekolah["lat"],
                    "end_lon": sekolah["lon"],
                    "name": sekolah["nama"],
                    "length": geo_length,
                    "time": round(15 * geo_length, 1),
                },
                "geometry": geometry,
            }
            return res_features
        else:
            return None

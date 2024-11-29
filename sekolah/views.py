from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from .models import Sekolah, SekolahMetadata
from .serializers import (
    SekolahDetailSerializer,
    SekolahMetadataSerializer,
    SekolahDetailSerializerWithMetadata,
    SekolahMetadataWithDataSerializer,
)
from geodjango.utils import csv_to_dict, calculate_bbox_from_csv_points


class SekolahMetadataList(generics.ListAPIView):
    queryset = SekolahMetadata.objects.all().order_by("created_at")
    serializer_class = SekolahMetadataSerializer


class SekolahMetadataDelete(generics.DestroyAPIView):
    queryset = SekolahMetadata.objects.all()
    serializer_class = SekolahMetadataSerializer


class SekolahMetadataDetail(generics.RetrieveAPIView):
    queryset = SekolahMetadata.objects.all()
    serializer_class = SekolahMetadataSerializer


class SekolahListByMetadataId(generics.RetrieveAPIView):
    queryset = SekolahMetadata.objects.all()
    serializer_class = SekolahMetadataWithDataSerializer

    def retrieve(self, request, *args, **kwargs):
        # Get the SekolahMetadata instance based on metadata_id
        metadata_instance = self.get_object()

        # Retrieve the Sekolah instances that correspond to the metadata_id
        sekolah_queryset = Sekolah.objects.filter(
            file_metadata=metadata_instance
        ).order_by("created_at")

        # Serialize the Sekolah instances
        sekolah_serializer = SekolahDetailSerializer(sekolah_queryset, many=True)

        # Serialize the SekolahMetadata instance
        metadata_serializer = self.get_serializer(metadata_instance)

        # Add the serialized Sekolah data to the metadata response
        response_data = metadata_serializer.data
        response_data["data"] = (
            sekolah_serializer.data
        )  # Add list of Sekolah under 'data'

        return Response(response_data)


class SekolahDetail(generics.RetrieveAPIView):
    queryset = Sekolah.objects.all()
    serializer_class = SekolahDetailSerializerWithMetadata


class SekolahUpload(generics.CreateAPIView):
    """
    API view to upload a csv file and metadata.
    Supported formats: .csv
    """

    def post(self, request, *args, **kwargs):
        # Get the uploaded file and metadata
        name = request.data.get("name")
        level = request.data.get("level")
        type = request.data.get("type")
        description = request.data.get("description")
        file = request.FILES.get("file")

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

        if not file:
            return Response(
                {"error": "File is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Process the file
        try:
            csv_data = csv_to_dict(file)
            bbox = calculate_bbox_from_csv_points(csv_data)
            # Save metadata (name, description) to the SekolahMetadata model
            metadata = SekolahMetadata.objects.create(
                name=name, level=level, type=type, description=description, bbox=bbox
            )

            for row in csv_data:
                lat = round(float(row["lat"]), 6)
                lon = round(float(row["lon"]), 6)

                # Create and save the Point to the database
                point = Point(lon, lat)
                sekolah = Sekolah(
                    tipe=row.get("tipe"),
                    npsn=row.get("npsn"),
                    nama=row.get("nama"),
                    alamat=row.get("alamat"),
                    kuota=int(row.get("kuota", 0)),
                    keterangan=row.get("keterangan"),
                    lat=lat,
                    lon=lon,
                    point=point,
                    file_metadata=metadata,
                )
                sekolah.save()

            return Response(
                {"message": "File uploaded successfully", "metadata_id": metadata.id},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SekolahDatumDelete(generics.DestroyAPIView):
    serializer_class = SekolahDetailSerializer

    def get_queryset(self):
        # Get the metadata_id and id from the URL
        metadata_id = self.kwargs.get("metadata_id")
        pk = self.kwargs.get("pk")
        # Filter the Sekolah objects by file_metadata_id and id
        return Sekolah.objects.filter(file_metadata_id=metadata_id, id=pk)


class SekolahDatumAdd(generics.CreateAPIView):
    """
    API view to add datum sekolah
    """

    def post(self, request, *args, **kwargs):
        # Get the metadata
        metadata_id = self.kwargs.get("pk")

        # Retrieve the metadata instance
        try:
            metadata = SekolahMetadata.objects.get(id=metadata_id)
        except SekolahMetadata.DoesNotExist:
            return Response(
                {"error": "Metadata not found."}, status=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        required_fields = ["tipe", "npsn", "nama", "lat", "lon", "kuota"]

        # Check for missing required fields
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Process the data
        try:
            lat = round(float(data["lat"]), 6)
            lon = round(float(data["lon"]), 6)

            # Create and save the Point to the database
            point = Point(lon, lat)
            sekolah = Sekolah(
                tipe=data["tipe"],
                npsn=data["npsn"],
                nama=data["nama"],
                alamat=data.get("alamat", ""),
                kuota=int(data["kuota"]),
                keterangan=data.get("keterangan", ""),
                lat=lat,
                lon=lon,
                point=point,
                file_metadata=metadata,
            )
            sekolah.save()

            return Response(
                {
                    "message": "Datum sekolah added successfully.",
                    "sekolah_id": sekolah.id,
                    "metadata_id": metadata_id,
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as ve:
            return Response(
                {"error": f"Invalid value: {ve}"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SekolahDatumEdit(generics.RetrieveAPIView):
    """
    API view to edit datum sekolah
    """

    def put(self, request, *args, **kwargs):
        # Get the uploaded file and metadata
        metadata_id = self.kwargs.get("metadata_id")
        sekolah_id = self.kwargs.get("pk")

        # Retrieve the metadata instance
        try:
            metadata = SekolahMetadata.objects.get(id=metadata_id)
        except SekolahMetadata.DoesNotExist:
            return Response(
                {"error": "Metadata not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Retrieve the Sekolah instance
        try:
            sekolah = Sekolah.objects.get(id=sekolah_id, file_metadata=metadata)
        except Sekolah.DoesNotExist:
            return Response(
                {"error": "Sekolah not found."}, status=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        required_fields = ["tipe", "npsn", "nama", "lat", "lon", "kuota"]

        # Check for missing required fields
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return Response(
                {"error": f"Missing fields: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Process the data
        try:
            lat = round(float(data["lat"]), 6)
            lon = round(float(data["lon"]), 6)

            # Update the Sekolah instance
            sekolah.tipe = data["tipe"]
            sekolah.npsn = data["npsn"]
            sekolah.nama = data["nama"]
            sekolah.alamat = data.get("alamat", "")
            sekolah.kuota = int(data["kuota"])
            sekolah.keterangan = data.get("keterangan", "")
            sekolah.lat = lat
            sekolah.lon = lon
            sekolah.point = Point(lon, lat)  # Update the Point field
            sekolah.save()

            return Response(
                {
                    "message": "Datum sekolah added successfully.",
                    "sekolah_id": sekolah.id,
                    "metadata_id": metadata_id,
                },
                status=status.HTTP_201_CREATED,
            )

        except ValueError as ve:
            return Response(
                {"error": f"Invalid value: {ve}"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from .models import PesertaDidik, PesertaDidikMetadata
from .serializers import (
    PesertaDidikDetailSerializer,
    PesertaDidikMetadataSerializer,
    PesertaDidikDetailSerializerWithMetadata,
    PesertaDidikMetadataWithDataSerializer,
)
from geodjango.utils import csv_to_dict, calculate_bbox_from_csv_points, parse_date


class PesertaDidikMetadataList(generics.ListAPIView):
    queryset = PesertaDidikMetadata.objects.all().order_by("created_at")
    serializer_class = PesertaDidikMetadataSerializer


class PesertaDidikMetadataDelete(generics.DestroyAPIView):
    queryset = PesertaDidikMetadata.objects.all()
    serializer_class = PesertaDidikMetadataSerializer


class PesertaDidikMetadataDetail(generics.RetrieveAPIView):
    queryset = PesertaDidikMetadata.objects.all()
    serializer_class = PesertaDidikMetadataSerializer


class PesertaDidikListByMetadataId(generics.RetrieveAPIView):
    queryset = PesertaDidikMetadata.objects.all()
    serializer_class = PesertaDidikMetadataWithDataSerializer

    def retrieve(self, request, *args, **kwargs):
        # Get the PesertaDidikMetadata instance based on metadata_id
        metadata_instance = self.get_object()

        # Retrieve the PesertaDidik instances that correspond to the metadata_id
        peserta_didik_queryset = PesertaDidik.objects.filter(
            file_metadata=metadata_instance
        ).order_by("created_at")

        # Serialize the PesertaDidik instances
        peserta_didik_serializer = PesertaDidikDetailSerializer(
            peserta_didik_queryset, many=True
        )

        # Serialize the PesertaDidikMetadata instance
        metadata_serializer = self.get_serializer(metadata_instance)

        # Add the serialized PesertaDidik data to the metadata response
        response_data = metadata_serializer.data
        response_data["data"] = (
            peserta_didik_serializer.data
        )  # Add list of PesertaDidik under 'data'

        return Response(response_data)


class PesertaDidikDetail(generics.RetrieveAPIView):
    queryset = PesertaDidik.objects.all()
    serializer_class = PesertaDidikDetailSerializerWithMetadata


class PesertaDidikUpload(generics.CreateAPIView):
    """
    API view to upload a csv file and metadata.
    Supported formats: .csv
    """

    def post(self, request, *args, **kwargs):
        # Get the uploaded file and metadata
        name = request.data.get("name")
        level = request.data.get("level")
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

        if not file:
            return Response(
                {"error": "File is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Process the file
        try:
            csv_data = csv_to_dict(file)
            bbox = calculate_bbox_from_csv_points(csv_data)
            # Save metadata (name, description) to the PesertaDidikMetadata model
            metadata = PesertaDidikMetadata.objects.create(
                name=name, level=level, description=description, bbox=bbox
            )

            for row in csv_data:
                lat = round(float(row["lat"]), 6)
                lon = round(float(row["lon"]), 6)

                # Create and save the Point to the database
                point = Point(lon, lat)
                peserta_didik = PesertaDidik(
                    nisn=row.get("nisn"),
                    nama=row.get("nama"),
                    jenis_kelamin=row.get("jenis_kelamin"),
                    tanggal_lahir=parse_date(row.get("tanggal_lahir")),
                    alamat=row.get("alamat"),
                    prioritas=int(row.get("prioritas", 0)),
                    keterangan=row.get("keterangan"),
                    lat=lat,
                    lon=lon,
                    point=point,
                    file_metadata=metadata,
                )
                peserta_didik.save()

            return Response(
                {"message": "File uploaded successfully", "metadata_id": metadata.id},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PesertaDidikDatumDelete(generics.DestroyAPIView):
    serializer_class = PesertaDidikDetailSerializer

    def get_queryset(self):
        # Get the metadata_id and id from the URL
        metadata_id = self.kwargs.get("metadata_id")
        pk = self.kwargs.get("pk")
        # Filter the PesertaDidik objects by file_metadata_id and id
        return PesertaDidik.objects.filter(file_metadata_id=metadata_id, id=pk)


class PesertaDidikDatumAdd(generics.CreateAPIView):
    """
    API view to add datum peserta_didik
    """

    def post(self, request, *args, **kwargs):
        # Get the metadata
        metadata_id = self.kwargs.get("pk")

        # Retrieve the metadata instance
        try:
            metadata = PesertaDidikMetadata.objects.get(id=metadata_id)
        except PesertaDidikMetadata.DoesNotExist:
            return Response(
                {"error": "Metadata not found."}, status=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        required_fields = [
            "nisn",
            "nama",
            "jenis_kelamin",
            "tanggal_lahir",
            "lat",
            "lon",
        ]

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
            peserta_didik = PesertaDidik(
                nisn=data["nisn"],
                nama=data["nama"],
                jenis_kelamin=data["jenis_kelamin"],
                tanggal_lahir=parse_date(data["tanggal_lahir"]),
                alamat=data.get("alamat", ""),
                prioritas=int(data["prioritas"]),
                keterangan=data.get("keterangan", ""),
                lat=lat,
                lon=lon,
                point=point,
                file_metadata=metadata,
            )
            peserta_didik.save()

            return Response(
                {
                    "message": "Datum peserta_didik added successfully.",
                    "peserta_didik_id": peserta_didik.id,
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


class PesertaDidikDatumEdit(generics.RetrieveAPIView):
    """
    API view to edit datum peserta_didik
    """

    def put(self, request, *args, **kwargs):
        # Get the uploaded file and metadata
        metadata_id = self.kwargs.get("metadata_id")
        peserta_didik_id = self.kwargs.get("pk")

        # Retrieve the metadata instance
        try:
            metadata = PesertaDidikMetadata.objects.get(id=metadata_id)
        except PesertaDidikMetadata.DoesNotExist:
            return Response(
                {"error": "Metadata not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Retrieve the PesertaDidik instance
        try:
            peserta_didik = PesertaDidik.objects.get(
                id=peserta_didik_id, file_metadata=metadata
            )
        except PesertaDidik.DoesNotExist:
            return Response(
                {"error": "PesertaDidik not found."}, status=status.HTTP_404_NOT_FOUND
            )

        data = request.data
        required_fields = [
            "nisn",
            "nama",
            "jenis_kelamin",
            "tanggal_lahir",
            "lat",
            "lon",
        ]

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

            # Update the PesertaDidik instance
            peserta_didik.nisn = data["nisn"]
            peserta_didik.nama = data["nama"]
            peserta_didik.jenis_kelamin = data["jenis_kelamin"]
            peserta_didik.tanggal_lahir = parse_date(data["tanggal_lahir"])
            peserta_didik.alamat = data.get("alamat", "")
            peserta_didik.prioritas = int(data["prioritas"])
            peserta_didik.keterangan = data.get("keterangan", "")
            peserta_didik.lat = lat
            peserta_didik.lon = lon
            peserta_didik.point = Point(lon, lat)  # Update the Point field
            peserta_didik.save()

            return Response(
                {
                    "message": "Datum peserta_didik added successfully.",
                    "peserta_didik_id": peserta_didik.id,
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

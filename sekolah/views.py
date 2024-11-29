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
        sekolah_queryset = Sekolah.objects.filter(file_metadata=metadata_instance)

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
            print("AAAAA")
            csv_data = csv_to_dict(file)
            print("BBBBBB")
            bbox = calculate_bbox_from_csv_points(csv_data)
            print("CCCCCC")
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

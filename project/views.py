from rest_framework import generics, status
from rest_framework.response import Response
from .models import ProjectMetadata
from .serializers import (
    ProjectMetadataSerializer,
)
from jalan.models import JalanMetadata


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
        print(project_level)
        if project_level:
            queryset = queryset.filter(level=project_level, status="PUBLISHED")
        else:
            queryset = queryset.filter(status="PUBLISHED")
        return queryset

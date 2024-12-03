from rest_framework import serializers
from .models import PesertaDidik, PesertaDidikMetadata


class PesertaDidikMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PesertaDidikMetadata
        fields = (
            "id",
            "name",
            "level",
            "description",
            "bbox",
            "created_at",
            "updated_at",
        )


class PesertaDidikDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PesertaDidik
        fields = (
            "id",
            "nisn",
            "nama",
            "jenis_kelamin",
            "tanggal_lahir",
            "alamat",
            "prioritas",
            "keterangan",
            "lat",
            "lon",
        )


class PesertaDidikDetailSerializerWithMetadata(serializers.ModelSerializer):
    file_metadata = (
        PesertaDidikMetadataSerializer()
    )  # Nested serializer for file metadata

    id = serializers.IntegerField()

    class Meta:
        model = PesertaDidik
        fields = (
            "id",
            "file_metadata",  # Include metadata in the response
            "nisn",
            "nama",
            "jenis_kelamin",
            "tanggal_lahir",
            "alamat",
            "prioritas",
            "keterangan",
            "lat",
            "lon",
        )


class PesertaDidikMetadataWithDataSerializer(serializers.ModelSerializer):
    # Add 'data' field to hold the list of PesertaDidik based on metadata_id
    data = PesertaDidikDetailSerializer(many=True, read_only=True)

    class Meta:
        model = PesertaDidikMetadata
        fields = (
            "id",
            "name",
            "level",
            "description",
            "bbox",
            "created_at",
            "updated_at",
            "data",
        )  # Include 'data' field

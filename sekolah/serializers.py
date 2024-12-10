from rest_framework import serializers
from .models import Sekolah, SekolahMetadata


class SekolahMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SekolahMetadata
        fields = (
            "id",
            "name",
            "level",
            "type",
            "zonasi",
            "description",
            "bbox",
            "created_at",
            "updated_at",
        )


class SekolahDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sekolah
        fields = (
            "id",
            "tipe",
            "npsn",
            "nama",
            "alamat",
            "kuota",
            "keterangan",
            "lat",
            "lon",
        )


class SekolahDetailSerializerWithMetadata(serializers.ModelSerializer):
    file_metadata = SekolahMetadataSerializer()  # Nested serializer for file metadata

    id = serializers.IntegerField()

    class Meta:
        model = Sekolah
        fields = (
            "id",
            "file_metadata",  # Include metadata in the response
            "tipe",
            "npsn",
            "nama",
            "alamat",
            "kuota",
            "keterangan",
            "lat",
            "lon",
        )


class SekolahMetadataWithDataSerializer(serializers.ModelSerializer):
    # Add 'data' field to hold the list of Sekolah based on metadata_id
    data = SekolahDetailSerializer(many=True, read_only=True)

    class Meta:
        model = SekolahMetadata
        fields = (
            "id",
            "name",
            "level",
            "type",
            "zonasi",
            "description",
            "bbox",
            "created_at",
            "updated_at",
            "data",
        )  # Include 'data' field

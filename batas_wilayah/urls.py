from django.urls import path
from .views import (
    BatasWilayahDetail,
    BatasWilayahListByMetadataId,
    BatasWilayahMetadataList,
    BatasWilayahMetadataDetail,
    BatasWilayahUpload,
    BatasWilayahMetadataDelete,
)

urlpatterns = [
    path(
        "batas-wilayah/upload/",
        BatasWilayahUpload.as_view(),
        name="batas-wilayah-upload",
    ),
    path(
        "batas-wilayah/delete/<str:pk>/",
        BatasWilayahMetadataDelete.as_view(),
        name="batas-wilayah-delete",
    ),
    path(
        "batas-wilayah/", BatasWilayahMetadataList.as_view(), name="batas-wilayah-list"
    ),
    path(
        "batas-wilayah/<str:pk>/",
        BatasWilayahMetadataDetail.as_view(),
        name="batas-wilayah-metadata-detail",
    ),
    path(
        "batas-wilayah/metadata/<str:metadata_id>/",
        BatasWilayahListByMetadataId.as_view(),
        name="batas-wilayah-list-by-metadata-id",
    ),
    path(
        "batas-wilayah/detail/<int:pk>/",
        BatasWilayahDetail.as_view(),
        name="batas-wilayah-detail",
    ),
]

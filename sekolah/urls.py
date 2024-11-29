from django.urls import path
from .views import (
    SekolahDetail,
    SekolahListByMetadataId,
    SekolahMetadataList,
    SekolahMetadataDetail,
    SekolahUpload,
    SekolahMetadataDelete,
)

urlpatterns = [
    path(
        "sekolah/upload/",
        SekolahUpload.as_view(),
        name="sekolah-upload",
    ),
    path(
        "sekolah/delete/<str:pk>/",
        SekolahMetadataDelete.as_view(),
        name="sekolah-delete",
    ),
    path("sekolah/", SekolahMetadataList.as_view(), name="sekolah-list"),
    path(
        "sekolah/<str:pk>/",
        SekolahMetadataDetail.as_view(),
        name="sekolah-metadata-detail",
    ),
    path(
        "sekolah/metadata/<str:pk>/",
        SekolahListByMetadataId.as_view(),
        name="sekolah-list-by-metadata-id",
    ),
    path(
        "sekolah/detail/<int:pk>/",
        SekolahDetail.as_view(),
        name="sekolah-detail",
    ),
]

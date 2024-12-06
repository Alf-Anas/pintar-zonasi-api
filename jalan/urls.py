from django.urls import path
from .views import (
    JalanMetadataList,
    JalanMetadataDetail,
    JalanMetadataDelete,
    JalanUpload,
    JalanGenerateTopology,
)

urlpatterns = [
    path(
        "jalan/upload/",
        JalanUpload.as_view(),
        name="jalan-upload",
    ),
    path(
        "jalan/delete/<str:pk>/",
        JalanMetadataDelete.as_view(),
        name="jalan-delete",
    ),
    path("jalan/", JalanMetadataList.as_view(), name="jalan-list"),
    path(
        "jalan/<str:pk>/",
        JalanMetadataDetail.as_view(),
        name="jalan-metadata-detail",
    ),
    path(
        "jalan/generate-topology/<str:pk>/",
        JalanGenerateTopology.as_view(),
        name="jalan-generate-topology",
    ),
]

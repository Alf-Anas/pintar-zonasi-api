from django.urls import path
from .views import (
    PesertaDidikDetail,
    PesertaDidikListByMetadataId,
    PesertaDidikMetadataList,
    PesertaDidikMetadataDetail,
    PesertaDidikUpload,
    PesertaDidikMetadataDelete,
    PesertaDidikDatumDelete,
    PesertaDidikDatumAdd,
    PesertaDidikDatumEdit,
)

urlpatterns = [
    path(
        "peserta-didik/upload/",
        PesertaDidikUpload.as_view(),
        name="peserta-didik-upload",
    ),
    path(
        "peserta-didik/delete/<str:pk>/",
        PesertaDidikMetadataDelete.as_view(),
        name="peserta-didik-delete",
    ),
    path(
        "peserta-didik/", PesertaDidikMetadataList.as_view(), name="peserta-didik-list"
    ),
    path(
        "peserta-didik/<str:pk>/",
        PesertaDidikMetadataDetail.as_view(),
        name="peserta-didik-metadata-detail",
    ),
    path(
        "peserta-didik/metadata/<str:pk>/",
        PesertaDidikListByMetadataId.as_view(),
        name="peserta-didik-list-by-metadata-id",
    ),
    path(
        "peserta-didik/detail/<int:pk>/",
        PesertaDidikDetail.as_view(),
        name="peserta-didik-detail",
    ),
    path(
        "peserta-didik/delete/<str:metadata_id>/<int:pk>/",
        PesertaDidikDatumDelete.as_view(),
        name="peserta-didik-delete-datum",
    ),
    path(
        "peserta-didik/add/<str:pk>/",
        PesertaDidikDatumAdd.as_view(),
        name="peserta-didik-add-datum",
    ),
    path(
        "peserta-didik/edit/<str:metadata_id>/<int:pk>/",
        PesertaDidikDatumEdit.as_view(),
        name="peserta-didik-edit-datum",
    ),
]

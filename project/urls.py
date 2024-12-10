from django.urls import path
from .views import (
    ProjectMetadataList,
    ProjectMetadataDetail,
    ProjectCreate,
    ProjectMetadataDelete,
    ProjectSaveLayer,
    ProjectUpdateStatus,
)

urlpatterns = [
    path(
        "project/create/",
        ProjectCreate.as_view(),
        name="project-create",
    ),
    path(
        "project/delete/<str:pk>/",
        ProjectMetadataDelete.as_view(),
        name="project-delete",
    ),
    path("project/", ProjectMetadataList.as_view(), name="project-list"),
    path(
        "project/<str:pk>/",
        ProjectMetadataDetail.as_view(),
        name="project-metadata-detail",
    ),
    path(
        "project/save-layer/<str:pk>/",
        ProjectSaveLayer.as_view(),
        name="project-save-layer",
    ),
    path(
        "project/update-status/<str:pk>/<str:status>/",
        ProjectUpdateStatus.as_view(),
        name="project-change-status",
    ),
]

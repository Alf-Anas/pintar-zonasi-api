from django.urls import path
from .views import WorldBorderList, WorldBorderDetail, WorldBorderUpload

urlpatterns = [
    path("worldborders/", WorldBorderList.as_view(), name="worldborder-list"),
    path(
        "worldborders/<int:pk>/", WorldBorderDetail.as_view(), name="worldborder-detail"
    ),
    path(
        "worldborders/upload/", WorldBorderUpload.as_view(), name="worldborder-upload"
    ),
]

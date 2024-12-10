from django.contrib import admin
from .models import ProjectMetadata

admin.site.register(ProjectMetadata, admin.ModelAdmin)

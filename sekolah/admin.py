from django.contrib import admin
from .models import Sekolah, SekolahMetadata

admin.site.register(Sekolah, admin.ModelAdmin)
admin.site.register(SekolahMetadata, admin.ModelAdmin)

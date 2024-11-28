from django.contrib import admin
from .models import BatasWilayah, BatasWilayahMetadata

admin.site.register(BatasWilayah, admin.ModelAdmin)
admin.site.register(BatasWilayahMetadata, admin.ModelAdmin)

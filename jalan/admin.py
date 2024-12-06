from django.contrib import admin
from .models import JalanMetadata, Jalan

admin.site.register(Jalan, admin.ModelAdmin)
admin.site.register(JalanMetadata, admin.ModelAdmin)

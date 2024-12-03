from django.contrib import admin
from .models import PesertaDidik, PesertaDidikMetadata

admin.site.register(PesertaDidik, admin.ModelAdmin)
admin.site.register(PesertaDidikMetadata, admin.ModelAdmin)

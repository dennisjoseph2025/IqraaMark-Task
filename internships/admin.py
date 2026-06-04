from django.contrib import admin
from .models import Internship


class InternshipAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'company', 'location', 'stipend', 'duration', 'created_at')
    list_filter = ('location', 'duration')
    search_fields = ('title', 'description', 'company__username')
    date_hierarchy = 'created_at'


admin.site.register(Internship, InternshipAdmin)

from django.contrib import admin
from .models import Application

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['student', 'internship', 'status', 'applied_at']
    list_filter = ['status', 'applied_at']
    search_fields = ['student__email', 'internship__title']
    ordering = ['-applied_at']
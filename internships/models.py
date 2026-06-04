from django.db import models
from django.conf import settings

class Internship(models.Model):
    company = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='internships',
        limit_choices_to={'role': 'company'}
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    stipend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    duration = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'internships'
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title
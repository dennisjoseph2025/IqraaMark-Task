from django.db import models
from django.conf import settings
from internships.models import Internship

class Application(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        limit_choices_to={'role': 'student'}
    )
    internship = models.ForeignKey(
        Internship,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'applications'
        unique_together = ('student', 'internship')
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['internship']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.student.email} -> {self.internship.title}"
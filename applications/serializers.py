from rest_framework import serializers
from .models import Application

class ApplicationSerializer(serializers.ModelSerializer):
    internship_title = serializers.CharField(source='internship.title', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'internship', 'internship_title', 'student', 'student_email', 'resume', 'status', 'applied_at']
        read_only_fields = ['id', 'student', 'student_email', 'status', 'applied_at']
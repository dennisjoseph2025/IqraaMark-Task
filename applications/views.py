from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Application
from .serializers import ApplicationSerializer

class ApplyInternshipView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'student':
            return Response({'error': 'Only students can apply for internships.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ApplicationSerializer(data=request.data)
        if serializer.is_valid():
            if Application.objects.filter(student=request.user, internship=serializer.validated_data['internship']).exists():
                return Response({'error': 'You have already applied for this internship.'}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(student=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListApplicationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'student':
            applications = Application.objects.filter(student=request.user).select_related('internship')
        elif request.user.role == 'company':
            applications = Application.objects.filter(internship__company=request.user).select_related('internship', 'student')
        else:
            return Response({'error': 'Invalid role.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ApplicationSerializer(applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UpdateApplicationStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        if request.user.role != 'company':
            return Response({'error': 'Only companies can update application status.'}, status=status.HTTP_403_FORBIDDEN)
        
        application = get_object_or_404(Application, pk=pk)
        
        if application.internship.company != request.user:
            return Response({'error': 'You can only update applications for your own internships.'}, status=status.HTTP_403_FORBIDDEN)
        
        new_status = request.data.get('status')
        if new_status not in ['pending', 'accepted', 'rejected']:
            return Response({'error': 'Invalid status. Choose from pending, accepted, rejected.'}, status=status.HTTP_400_BAD_REQUEST)
        
        application.status = new_status
        application.save()
        serializer = ApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)
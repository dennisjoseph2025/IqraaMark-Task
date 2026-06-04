from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Internship
from .serializers import InternshipSerializer

class InternshipListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get(self, request):
        internships = Internship.objects.select_related('company').all()
        serializer = InternshipSerializer(internships, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'company':
            return Response({'error': 'Only companies can create internships.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = InternshipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(company=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InternshipDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Internship, pk=pk)

    def put(self, request, pk):
        internship = self.get_object(pk)
        if internship.company != request.user:
            return Response({'error': 'You do not have permission to update this internship.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = InternshipSerializer(internship, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        internship = self.get_object(pk)
        if internship.company != request.user:
            return Response({'error': 'You do not have permission to delete this internship.'}, status=status.HTTP_403_FORBIDDEN)
        internship.delete()
        return Response({'message': 'Internship deleted.'}, status=status.HTTP_204_NO_CONTENT)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import University, AcademicUnit, TeacherDesignation
from .serializers import (
    UniversitySerializer, AcademicUnitSerializer, TeacherDesignationSerializer
)
from accounts.models import User
from accounts.serializers import UserListSerializer

class UniversityListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        universities = University.objects.all()
        serializer = UniversitySerializer(universities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AcademicUnitListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        unit_type = request.query_params.get('unit_type')
        unit_type = unit_type.lower()

        short_name = request.query_params.get('short_name')
        short_name = short_name.upper()

        queryset = AcademicUnit.objects.all()
        
        # Filter by unit_type if provided
        if unit_type in ['department', 'institute']:
            queryset = queryset.filter(unit_type=unit_type)
        elif unit_type and unit_type not in ['department', 'institute']:
            return Response(
                {"message": "Invalid unit_type. Use 'department' or 'institute'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Filter by university short_name if provided
        if short_name:
            try:
                university = University.objects.get(short_name=short_name)
                queryset = queryset.filter(university=university)
            except University.DoesNotExist:
                return Response(
                    {"message": "University not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        serializer = AcademicUnitSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TeacherDesignationListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        designations = TeacherDesignation.objects.all()
        serializer = TeacherDesignationSerializer(designations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UniversityUsersView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, university_short_name):
        try:
            university = University.objects.get(short_name=university_short_name.upper())
            students = User.objects.filter(role='student', university=university)
            teachers = User.objects.filter(role='teacher', university=university)
            officers = User.objects.filter(role='officer', university=university)
            staff = User.objects.filter(role='staff', university=university)
            response_data = {
                'students': UserListSerializer(students, many=True, context={'request': request}).data,
                'teachers': UserListSerializer(teachers, many=True, context={'request': request}).data,
                'officers': UserListSerializer(officers, many=True, context={'request': request}).data,
                'staff': UserListSerializer(staff, many=True, context={'request': request}).data
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except University.DoesNotExist:
            return Response({"message": "University not found."}, status=status.HTTP_404_NOT_FOUND) 
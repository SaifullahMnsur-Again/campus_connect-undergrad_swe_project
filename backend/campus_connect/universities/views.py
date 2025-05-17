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
        
        if unit_type in ['department', 'institute']:
            queryset = queryset.filter(unit_type=unit_type)
        elif unit_type and unit_type not in ['department', 'institute']:
            return Response(
                {"message": "Invalid unit_type. Use 'department' or 'institute'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
            users = User.objects.filter(university=university).select_related('university', 'academic_unit')
            response_data = {
                'students': [],
                'teachers': [],
                'officers': [],
                'staff': []
            }
            for user in users:
                serialized = UserListSerializer(user, context={'request': request}).data
                if user.role == 'student':
                    response_data['students'].append(serialized)
                elif user.role == 'teacher':
                    response_data['teachers'].append(serialized)
                elif user.role == 'officer':
                    response_data['officers'].append(serialized)
                elif user.role == 'staff':
                    response_data['staff'].append(serialized)
            return Response(response_data, status=status.HTTP_200_OK)
        except University.DoesNotExist:
            return Response({"message": "University not found."}, status=status.HTTP_404_NOT_FOUND)
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

class DepartmentListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        departments = AcademicUnit.objects.filter(unit_type='department')
        serializer = AcademicUnitSerializer(departments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class InstituteListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        institutes = AcademicUnit.objects.filter(unit_type='institute')
        serializer = AcademicUnitSerializer(institutes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TeacherDesignationListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        designations = TeacherDesignation.objects.all()
        serializer = TeacherDesignationSerializer(designations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DepartmentInstituteListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        university_id = request.query_params.get('university_id')
        if university_id:
            try:
                university = University.objects.get(id=university_id)
                departments = AcademicUnit.objects.filter(university=university, unit_type='department')
                institutes = AcademicUnit.objects.filter(university=university, unit_type='institute')
            except University.DoesNotExist:
                return Response({"message": "University not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            departments = AcademicUnit.objects.filter(unit_type='department')
            institutes = AcademicUnit.objects.filter(unit_type='institute')
        return Response({
            'departments': AcademicUnitSerializer(departments, many=True).data,
            'institutes': AcademicUnitSerializer(institutes, many=True).data
        }, status=status.HTTP_200_OK)

class UniversityUsersView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, university_short_name):
        try:
            university = University.objects.get(short_name=university_short_name)
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
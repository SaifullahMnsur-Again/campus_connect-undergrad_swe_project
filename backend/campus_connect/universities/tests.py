from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from .models import University, Department, Institute, TeacherDesignation
from rest_framework.authtoken.models import Token
from accounts.models import VerificationCode
from bloodbank.models import BloodGroup

class UniversityAPITestCase(TestCase):
    # universities/tests.py, around line ~40
    def setUp(self):
        self.client = APIClient()
        self.university = University.objects.create(name="University of Dhaka")
        self.university2 = University.objects.create(name="BUET")
        self.department = Department.objects.create(name="Department of Pharmacy", university=self.university)
        self.institute = Institute.objects.create(name="Institute of Business Administration", university=self.university)
        self.teacher_designation = TeacherDesignation.objects.create(name="Professor")
        self.blood_group = BloodGroup.objects.create(name="A+")
        self.student = User.objects.create_user(
            email="student@example.com",
            password="password123",
            name="Student User",
            role="student",
            university=self.university,
            department=self.department,
            is_active=True,
            is_verified=True
        )
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            password="password123",
            name="Teacher User",
            role="teacher",
            university=self.university,
            institute=self.institute,
            teacher_designation=self.teacher_designation,
            contact_visibility="email",  # Added
            is_active=True,
            is_verified=True
        )
        self.officer = User.objects.create_user(
            email="officer@example.com",
            password="password123",
            name="Officer User",
            role="officer",
            designation="Registrar",
            workplace="Administration Office",
            is_active=True,
            is_verified=True
        )
        self.token = Token.objects.create(user=self.student)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    # Around line ~113
    def test_get_university_users(self):
        """Test retrieving users by role for a university."""
        response = self.client.get(reverse('university-users', args=[self.university.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['students']), 1)
        self.assertEqual(len(response.data['teachers']), 1)
        self.assertEqual(len(response.data['officers']), 0)
        self.assertEqual(len(response.data['staff']), 0)
        self.assertEqual(response.data['students'][0]['name'], "Student User")
        self.assertEqual(response.data['teachers'][0]['name'], "Teacher User")  # Changed from email to name

    def test_get_departments(self):
        """Test retrieving list of departments."""
        response = self.client.get(reverse('department-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Department of Pharmacy")

    def test_get_institutes(self):
        """Test retrieving list of institutes."""
        response = self.client.get(reverse('institute-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Institute of Business Administration")

    def test_get_teacher_designations(self):
        """Test retrieving list of teacher designations."""
        response = self.client.get(reverse('teacher-designation-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], "Professor")

    def test_get_departments_institutes(self):
        """Test retrieving departments and institutes for a university."""
        response = self.client.get(reverse('department-institute-list'), {'university_id': self.university.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['departments']), 1)
        self.assertEqual(len(response.data['institutes']), 1)
        self.assertEqual(response.data['departments'][0]['name'], "Department of Pharmacy")
        self.assertEqual(response.data['institutes'][0]['name'], "Institute of Business Administration")

    def test_get_departments_institutes_no_filter(self):
        """Test retrieving all departments and institutes without university filter."""
        response = self.client.get(reverse('department-institute-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['departments']), 1)
        self.assertEqual(len(response.data['institutes']), 1)

    def test_get_departments_institutes_invalid_university(self):
        """Test retrieving departments and institutes for a non-existent university."""
        response = self.client.get(reverse('department-institute-list'), {'university_id': 999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "University not found.")

    def test_get_university_users(self):
        """Test retrieving users by role for a university."""
        response = self.client.get(reverse('university-users', args=[self.university.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['students']), 1)
        self.assertEqual(len(response.data['teachers']), 1)
        self.assertEqual(len(response.data['officers']), 0)
        self.assertEqual(len(response.data['staff']), 0)
        self.assertEqual(response.data['students'][0]['email'], "student@example.com")
        self.assertEqual(response.data['teachers'][0]['email'], "teacher@example.com")

    def test_get_university_users_invalid_university(self):
        """Test retrieving users for a non-existent university."""
        response = self.client.get(reverse('university-users', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['message'], "University not found.")

    def test_get_university_users_unauthenticated(self):
        """Test retrieving university users without authentication."""
        self.client.credentials()
        response = self.client.get(reverse('university-users', args=[self.university.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['students']), 1)
        self.assertEqual(len(response.data['teachers']), 1)

    def test_unauthenticated_access_university_list(self):
        """Test accessing university list without authentication."""
        self.client.credentials()
        response = self.client.get(reverse('university-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_unauthenticated_access_department_list(self):
        """Test accessing department list without authentication."""
        self.client.credentials()
        response = self.client.get(reverse('department-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unauthenticated_access_institute_list(self):
        """Test accessing institute list without authentication."""
        self.client.credentials()
        response = self.client.get(reverse('institute-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
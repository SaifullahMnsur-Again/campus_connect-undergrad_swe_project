from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from accounts.models import User, VerificationCode
from bloodbank.models import BloodGroup
from universities.models import University, Department, Institute, TeacherDesignation
from rest_framework.authtoken.models import Token

class AccountsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.blood_group = BloodGroup.objects.create(name="A+")
        self.university = University.objects.create(name="University of Dhaka")
        self.department = Department.objects.create(name="Department of Pharmacy", university=self.university)
        self.institute = Institute.objects.create(name="Institute of Business Administration", university=self.university)
        self.teacher_designation = TeacherDesignation.objects.create(name="Professor")
        self.user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "blood_group": "A+",
            "role": "student",
            "university": self.university.id,
            "department": self.department.id
        }
        self.other_user_data = {
            "name": "Other User",
            "email": "other@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "blood_group": "A+",
            "role": "teacher",
            "university": self.university.id,
            "institute": self.institute.id,
            "teacher_designation": self.teacher_designation.id
        }
        self.officer_data = {
            "name": "Officer User",
            "email": "officer@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "blood_group": "A+",
            "role": "officer",
            "designation": "Registrar",
            "workplace": "Administration Office"
        }
        self.blank_user_data = {
            "name": "Blank User",
            "email": "blank@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "blood_group": "A+",
            "role": "student"
        }
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="admin123",
            name="Admin User"
        )

    def test_register_user_success(self):
        """Test successful user registration with university affiliation."""
        response = self.client.post(reverse('register'), self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User registered, please verify your email.")
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())
        self.assertTrue(VerificationCode.objects.filter(user__email=self.user_data["email"]).exists())
        user = User.objects.get(email=self.user_data["email"])
        self.assertEqual(user.role, "student")
        self.assertEqual(user.university, self.university)
        self.assertEqual(user.department, self.department)
        self.assertIsNone(user.institute)

    def test_register_user_duplicate_email(self):
        """Test registration with an existing email."""
        self.client.post(reverse('register'), self.user_data, format='json')
        response = self.client.post(reverse('register'), self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["message"])

    def test_register_user_invalid_blood_group(self):
        """Test registration with invalid blood group."""
        data = self.user_data.copy()
        data["blood_group"] = "Invalid"
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blood_group", response.data["message"])

    def test_register_user_invalid_university_affiliation(self):
        """Test registration with invalid university affiliation (both department and institute)."""
        data = self.user_data.copy()
        data["department"] = self.department.id
        data["institute"] = self.institute.id
        response = self.client.post(reverse('register'), data, format='json')
        print(response.data)  # Debug output
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("department", response.data["message"])
        self.assertIn("institute", response.data["message"])
        self.assertEqual(
            str(response.data["message"]["department"][0]),  # Access first element and convert to string
            "Cannot select both a department and an institute."
        )
        self.assertEqual(
            str(response.data["message"]["institute"][0]),  # Access first element and convert to string
            "Cannot select both a department and an institute."
        )

    def test_register_teacher_with_institute(self):
        """Test registering a teacher with university and institute."""
        response = self.client.post(reverse('register'), self.other_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=self.other_user_data["email"])
        self.assertEqual(user.role, "teacher")
        self.assertEqual(user.university, self.university)
        self.assertEqual(user.institute, self.institute)
        self.assertIsNone(user.department)
        self.assertEqual(user.teacher_designation, self.teacher_designation)

    def test_register_officer(self):
        """Test registering an officer with designation and workplace."""
        response = self.client.post(reverse('register'), self.officer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=self.officer_data["email"])
        self.assertEqual(user.role, "officer")
        self.assertEqual(user.designation, "Registrar")
        self.assertEqual(user.workplace, "Administration Office")
        self.assertIsNone(user.university)

    def test_register_blank_university(self):
        """Test registering a student with no university affiliation."""
        response = self.client.post(reverse('register'), self.blank_user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=self.blank_user_data["email"])
        self.assertEqual(user.role, "student")
        self.assertIsNone(user.university)
        self.assertIsNone(user.department)
        self.assertIsNone(user.institute)

    def test_email_verification_success(self):
        """Test successful email verification."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        data = {"email": self.user_data["email"], "code": code}
        response = self.client.post(reverse('verify-email'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Email verified successfully.")
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)

    def test_email_verification_invalid_code(self):
        """Test email verification with invalid code."""
        self.client.post(reverse('register'), self.user_data, format='json')
        data = {"email": self.user_data["email"], "code": "123456"}
        response = self.client.post(reverse('verify-email'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid or expired code.")

    def test_email_verification_expired_code(self):
        """Test email verification with expired code."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        verification = VerificationCode.objects.get(user=user)
        verification.expires_at = timezone.now() - timedelta(minutes=1)
        verification.save()
        data = {"email": self.user_data["email"], "code": verification.code}
        response = self.client.post(reverse('verify-email'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid or expired code.")

    def test_login_success(self):
        """Test successful login after verification."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
        response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "password123"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["id"], user.id)
        self.assertEqual(response.data["user"]["name"], self.user_data["name"])
        self.assertEqual(response.data["user"]["role"], "student")
        self.assertEqual(response.data["user"]["university"], self.university.name)

    def test_login_unverified_user(self):
        """Test login with unverified user."""
        self.client.post(reverse('register'), self.user_data, format='json')
        response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "password123"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Account is inactive or unverified.")

    def test_login_invalid_credentials(self):
        """Test login with invalid password."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
        response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid credentials.")

    def test_logout_success(self):
        """Test successful logout."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
        login_response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "password123"
        })
        token = login_response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Logged out successfully.")
        self.assertFalse(Token.objects.filter(user=user).exists())

    def test_logout_unauthenticated(self):
        """Test logout without authentication."""
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_get_success(self):
        """Test retrieving authenticated user's profile with university details."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
        login_response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "password123"
        })
        token = login_response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user_data["email"])
        self.assertEqual(response.data["name"], self.user_data["name"])
        self.assertEqual(response.data["role"], "student")
        self.assertEqual(response.data["university"], self.university.name)
        self.assertEqual(response.data["department"], self.department.name)
        self.assertIsNone(response.data["institute"])

    def test_profile_get_unauthenticated(self):
        """Test profile retrieval without authentication."""
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # accounts/tests.py, line ~270
def test_profile_update_success(self):
    """Test updating authenticated user's profile with university details."""
    self.client.post(reverse('register'), self.user_data, format='json')
    user = User.objects.get(email=self.user_data["email"])
    code = VerificationCode.objects.get(user=user).code
    self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
    login_response = self.client.post(reverse('login'), {
        "email": self.user_data["email"],
        "password": "password123"
    })
    token = login_response.data["token"]
    self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    update_data = {
        "name": "Updated Name",
        "contact_visibility": "email",
        "role": "teacher",
        "university": self.university.id,
        "institute": self.institute.id,  # Removed department
        "teacher_designation": self.teacher_designation.id
    }
    response = self.client.patch(reverse('user-profile'), update_data, format='json')
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response.data["message"], "Profile updated successfully.")
    self.assertEqual(response.data["data"]["name"], "Updated Name")
    self.assertEqual(response.data["data"]["contact_visibility"], "email")
    self.assertEqual(response.data["data"]["role"], "teacher")
    self.assertEqual(response.data["data"]["university"], self.university.name)
    self.assertEqual(response.data["data"]["institute"], self.institute.name)
    self.assertIsNone(response.data["data"]["department"])

    def test_profile_update_invalid_data(self):
        """Test profile update with invalid data."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
        login_response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "password123"
        })
        token = login_response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        update_data = {"phone": "invalid_phone"}
        response = self.client.patch(reverse('user-profile'), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data["message"])

    def test_profile_update_invalid_university_data(self):
        """Test profile update with invalid university affiliation data."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
        login_response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "password123"
        })
        token = login_response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        update_data = {
            "role": "student",
            "university": self.university.id,
            "department": self.department.id,
            "institute": self.institute.id
        }
        response = self.client.patch(reverse('user-profile'), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("department", response.data["message"])
        self.assertIn("institute", response.data["message"])

    # accounts/tests.py, around line ~330
    def test_user_list_unauthenticated(self):
        """Test user list retrieval without authentication."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["results"]) > 0)
        self.assertEqual(response.data["results"][0]["role"], "student")
        self.assertEqual(response.data["results"][0]["university"], self.university.name)

    def test_user_list_pagination(self):
        """Test user list pagination with university details."""
        for i in range(5):
            data = {
                "name": f"User {i}",
                "email": f"user{i}@example.com",
                "password": "password123",
                "confirm_password": "password123",
                "blood_group": "A+",
                "role": "student",
                "university": self.university.id,
                "department": self.department.id
            }
            self.client.post(reverse('register'), data, format='json')
        response = self.client.get(reverse('user-list'), {"limit": 2, "offset": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"][0]["role"], "student")

    def test_user_detail_get_success(self):
        """Test retrieving another user's profile with university details."""
        self.client.post(reverse('register'), self.other_user_data, format='json')
        other_user = User.objects.get(email=self.other_user_data["email"])
        code = VerificationCode.objects.get(user=other_user).code
        self.client.post(reverse('verify-email'), {"email": self.other_user_data["email"], "code": code})
        response = self.client.get(reverse('user-detail', args=[other_user.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.other_user_data["name"])
        self.assertEqual(response.data["role"], "teacher")
        self.assertEqual(response.data["university"], self.university.name)
        self.assertEqual(response.data["institute"], self.institute.name)
        self.assertIsNone(response.data["department"])
        self.assertNotIn("email", response.data)  # Default visibility is 'none'

    def test_user_detail_get_not_found(self):
        """Test retrieving non-existent user's profile."""
        response = self.client.get(reverse('user-detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "User not found.")

    def test_user_detail_patch_not_allowed(self):
        """Test that PATCH requests to user-detail are not allowed."""
        self.client.post(reverse('register'), self.user_data, format='json')
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
        login_response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "password123"
        })
        token = login_response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        update_data = {"name": "Updated Name"}
        response = self.client.patch(reverse('user-detail', args=[user.pk]), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], "Method \"PATCH\" not allowed.")

    def test_profile_create_university_affiliation(self):
        """Test creating university affiliation for user without one."""
        data = {
            "name": "No Profile User",
            "email": "noprofile@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "blood_group": "A+"
        }
        self.client.post(reverse('register'), data, format='json')
        user = User.objects.get(email="noprofile@example.com")
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": "noprofile@example.com", "code": code})
        login_response = self.client.post(reverse('login'), {
            "email": "noprofile@example.com",
            "password": "password123"
        })
        token = login_response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        update_data = {
            "role": "student",
            "university": self.university.id,
            "department": self.department.id
        }
        response = self.client.patch(reverse('user-profile'), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["role"], "student")
        self.assertEqual(response.data["data"]["university"], self.university.name)
        self.assertEqual(response.data["data"]["department"], self.department.name)
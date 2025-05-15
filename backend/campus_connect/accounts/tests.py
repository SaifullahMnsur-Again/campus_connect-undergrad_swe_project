from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from accounts.models import User, VerificationCode
from bloodbank.models import BloodGroup, Donor
import uuid
from rest_framework.authtoken.models import Token

class AccountsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.blood_group = BloodGroup.objects.create(name="A+")
        self.user_data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "blood_group": "A+"
        }
        self.other_user_data = {
            "name": "Other User",
            "email": "other@example.com",
            "password": "password123",
            "confirm_password": "password123",
            "blood_group": "A+"
        }
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="admin123",
            name="Admin User"
        )

    def test_register_user_success(self):
        """Test successful user registration."""
        response = self.client.post(reverse('register'), self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "User registered, please verify your email.")
        self.assertTrue(User.objects.filter(email=self.user_data["email"]).exists())
        self.assertTrue(VerificationCode.objects.filter(user__email=self.user_data["email"]).exists())

    def test_register_user_duplicate_email(self):
        """Test registration with an existing email."""
        self.client.post(reverse('register'), self.user_data)
        response = self.client.post(reverse('register'), self.user_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data["message"])

    def test_register_user_invalid_blood_group(self):
        """Test registration with invalid blood group."""
        data = self.user_data.copy()
        data["blood_group"] = "Invalid"
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("blood_group", response.data["message"])

    def test_email_verification_success(self):
        """Test successful email verification."""
        self.client.post(reverse('register'), self.user_data)
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
        self.client.post(reverse('register'), self.user_data)
        data = {"email": self.user_data["email"], "code": "123456"}
        response = self.client.post(reverse('verify-email'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Invalid or expired code.")

    def test_email_verification_expired_code(self):
        """Test email verification with expired code."""
        self.client.post(reverse('register'), self.user_data)
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
        self.client.post(reverse('register'), self.user_data)
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

    def test_login_unverified_user(self):
        """Test login with unverified user."""
        self.client.post(reverse('register'), self.user_data)
        response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "password123"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Account is inactive or unverified.")

    def test_login_invalid_credentials(self):
        """Test login with invalid password."""
        self.client.post(reverse('register'), self.user_data)
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
        self.client.post(reverse('register'), self.user_data)
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
        """Test retrieving authenticated user's profile."""
        self.client.post(reverse('register'), self.user_data)
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

    def test_profile_get_unauthenticated(self):
        """Test profile retrieval without authentication."""
        response = self.client.get(reverse('user-profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_update_success(self):
        """Test updating authenticated user's profile."""
        self.client.post(reverse('register'), self.user_data)
        user = User.objects.get(email=self.user_data["email"])
        code = VerificationCode.objects.get(user=user).code
        self.client.post(reverse('verify-email'), {"email": self.user_data["email"], "code": code})
        login_response = self.client.post(reverse('login'), {
            "email": self.user_data["email"],
            "password": "password123"
        })
        token = login_response.data["token"]
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        update_data = {"name": "Updated Name", "contact_visibility": "email"}
        response = self.client.patch(reverse('user-profile'), update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Profile updated successfully.")
        self.assertEqual(response.data["data"]["name"], "Updated Name")
        self.assertEqual(response.data["data"]["contact_visibility"], "email")

    def test_profile_update_invalid_data(self):
        """Test profile update with invalid data."""
        self.client.post(reverse('register'), self.user_data)
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
        response = self.client.patch(reverse('user-profile'), update_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("phone", response.data["message"])

    def test_user_list_unauthenticated(self):
        """Test user list retrieval without authentication."""
        User.objects.create_user(
            email="user2@example.com",
            password="password123",
            name="User Two",
            is_active=True,
            is_verified=True
        )
        response = self.client.get(reverse('user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_user_list_pagination(self):
        """Test user list pagination."""
        for i in range(5):
            User.objects.create_user(
                email=f"user{i}@example.com",
                password="password123",
                name=f"User {i}",
                is_active=True,
                is_verified=True
            )
        response = self.client.get(reverse('user-list'), {"limit": 2, "offset": 0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_user_detail_get_success(self):
        """Test retrieving another user's profile."""
        self.client.post(reverse('register'), self.other_user_data)
        other_user = User.objects.get(email=self.other_user_data["email"])
        code = VerificationCode.objects.get(user=other_user).code
        self.client.post(reverse('verify-email'), {"email": self.other_user_data["email"], "code": code})
        response = self.client.get(reverse('user-detail', args=[other_user.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.other_user_data["name"])
        # Check visibility restrictions
        self.assertNotIn("email", response.data)  # Default visibility is 'none'

    def test_user_detail_get_not_found(self):
        """Test retrieving non-existent user's profile."""
        response = self.client.get(reverse('user-detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "User not found.")

    def test_user_detail_patch_not_allowed(self):
        """Test that PATCH requests to user-detail are not allowed."""
        self.client.post(reverse('register'), self.user_data)
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
        response = self.client.patch(reverse('user-detail', args=[user.pk]), update_data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], "Method \"PATCH\" not allowed.")
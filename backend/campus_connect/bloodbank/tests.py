from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
from accounts.models import User
from bloodbank.models import BloodGroup, Donor
import uuid

class BloodbankAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.blood_group = BloodGroup.objects.create(name="A+")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="Test User",
            is_active=True,
            is_verified=True,
            blood_group=self.blood_group
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="password123",
            name="Other User",
            is_active=True,
            is_verified=True,
            blood_group=self.blood_group
        )
        self.donor_data = {
            "emergency_contact": "+1234567890",
            "preferred_location": "Local Hospital",
            "last_donated": "2025-01-01",
            "consent": True
        }

    def test_blood_group_list(self):
        """Test retrieving blood group list."""
        BloodGroup.objects.create(name="B+")
        response = self.client.get(reverse('bloodgroup-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("A+", response.data)
        self.assertIn("B+", response.data)

    def test_blood_group_detail(self):
        """Test retrieving single blood group."""
        response = self.client.get(reverse('bloodgroup-detail', args=[self.blood_group.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "A+")

    def test_blood_group_detail_not_found(self):
        """Test retrieving non-existent blood group."""
        response = self.client.get(reverse('bloodgroup-detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Blood group not found.")

    def test_donor_register_success(self):
        """Test successful donor registration."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('donor-register'), self.donor_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["emergency_contact"], self.donor_data["emergency_contact"])
        self.assertTrue(Donor.objects.filter(user=self.user).exists())

    def test_donor_register_already_exists(self):
        """Test donor registration when already registered."""
        self.client.force_authenticate(user=self.user)
        Donor.objects.create(
            user=self.user,
            emergency_contact="+1234567890",
            preferred_location="Local Hospital",
            consent=True
        )
        response = self.client.post(reverse('donor-register'), self.donor_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "User is already registered as a donor.")

    def test_donor_register_unauthenticated(self):
        """Test donor registration without authentication."""
        response = self.client.post(reverse('donor-register'), self.donor_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_donor_register_invalid_data(self):
        """Test donor registration with invalid data."""
        self.client.force_authenticate(user=self.user)
        invalid_data = self.donor_data.copy()
        invalid_data["emergency_contact"] = "invalid_phone"
        response = self.client.post(reverse('donor-register'), invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("emergency_contact", response.data)

    def test_donor_profile_get_success(self):
        """Test retrieving donor profile via donor/ and donor/profile/."""
        self.client.force_authenticate(user=self.user)
        Donor.objects.create(
            user=self.user,
            emergency_contact="+1234567890",
            preferred_location="Local Hospital",
            consent=True
        )
        # Test donor/
        response = self.client.get(reverse('donor-profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["emergency_contact"], "+1234567890")
        self.assertEqual(response.data["name"], self.user.name)
        # Test donor/profile/
        response = self.client.get(reverse('donor-profile-explicit'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["emergency_contact"], "+1234567890")
        self.assertEqual(response.data["name"], self.user.name)

    def test_donor_profile_get_no_profile(self):
        """Test retrieving non-existent donor profile via donor/ and donor/profile/."""
        self.client.force_authenticate(user=self.user)
        # Test donor/
        response = self.client.get(reverse('donor-profile'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "No donor profile found. To register as a donor use the url below.")
        self.assertEqual(response.data["redirect"], f"http://testserver{reverse('donor-register')}")
        # Test donor/profile/
        response = self.client.get(reverse('donor-profile-explicit'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "No donor profile found. To register as a donor use the url below.")
        self.assertEqual(response.data["redirect"], f"http://testserver{reverse('donor-register')}")

    def test_donor_profile_update_success(self):
        """Test updating donor profile via donor/ and donor/profile/."""
        self.client.force_authenticate(user=self.user)
        Donor.objects.create(
            user=self.user,
            emergency_contact="+1234567890",
            preferred_location="Local Hospital",
            consent=True
        )
        update_data = {"preferred_location": "New Hospital", "consent": False}
        # Test donor/
        response = self.client.patch(reverse('donor-profile'), update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Donor profile updated successfully.")
        self.assertEqual(response.data["data"]["preferred_location"], "New Hospital")
        self.assertEqual(response.data["data"]["consent"], False)
        # Test donor/profile/
        response = self.client.patch(reverse('donor-profile-explicit'), update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Donor profile updated successfully.")
        self.assertEqual(response.data["data"]["preferred_location"], "New Hospital")
        self.assertEqual(response.data["data"]["consent"], False)

    def test_donor_profile_update_no_profile(self):
        """Test updating non-existent donor profile via donor/ and donor/profile/."""
        self.client.force_authenticate(user=self.user)
        update_data = {"preferred_location": "New Hospital"}
        # Test donor/
        response = self.client.patch(reverse('donor-profile'), update_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "No donor profile found. To register as a donor use the url below.")
        self.assertEqual(response.data["redirect"], f"http://testserver{reverse('donor-register')}")
        # Test donor/profile/
        response = self.client.patch(reverse('donor-profile-explicit'), update_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "No donor profile found. To register as a donor use the url below.")
        self.assertEqual(response.data["redirect"], f"http://testserver{reverse('donor-register')}")

    def test_donor_profile_update_invalid_data(self):
        """Test updating donor profile with invalid data."""
        self.client.force_authenticate(user=self.user)
        Donor.objects.create(
            user=self.user,
            emergency_contact="+1234567890",
            preferred_location="Local Hospital",
            consent=True
        )
        update_data = {"emergency_contact": "invalid_phone"}
        # Test donor/
        response = self.client.patch(reverse('donor-profile'), update_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("emergency_contact", response.data)
        # Test donor/profile/
        response = self.client.patch(reverse('donor-profile-explicit'), update_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("emergency_contact", response.data)

    def test_donor_withdraw_success(self):
        """Test withdrawing donor profile."""
        self.client.force_authenticate(user=self.user)
        Donor.objects.create(
            user=self.user,
            emergency_contact="+1234567890",
            preferred_location="Local Hospital",
            consent=True
        )
        response = self.client.post(reverse('donor-withdraw'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data["message"], "Donor profile withdrawn successfully.")
        self.assertFalse(Donor.objects.filter(user=self.user).exists())

    def test_donor_withdraw_no_profile(self):
        """Test withdrawing non-existent donor profile."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse('donor-withdraw'))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "No donor profile found.")

    def test_donor_detail_get_success(self):
        """Test retrieving another donor's profile."""
        self.client.force_authenticate(user=self.user)
        donor = Donor.objects.create(
            user=self.other_user,
            emergency_contact="+1234567890",
            preferred_location="Local Hospital",
            consent=True
        )
        response = self.client.get(reverse('donor-detail', args=[donor.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["emergency_contact"], "+1234567890")
        self.assertEqual(response.data["name"], self.other_user.name)

    def test_donor_detail_get_not_found(self):
        """Test retrieving non-existent donor profile."""
        response = self.client.get(reverse('donor-detail', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Donor profile not found.")

    def test_donor_detail_patch_not_allowed(self):
        """Test that PATCH requests to donor-detail are not allowed."""
        self.client.force_authenticate(user=self.user)
        donor = Donor.objects.create(
            user=self.user,
            emergency_contact="+1234567890",
            preferred_location="Local Hospital",
            consent=True
        )
        update_data = {"preferred_location": "New Hospital"}
        response = self.client.patch(reverse('donor-detail', args=[donor.pk]), update_data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.data["detail"], "Method \"PATCH\" not allowed.")
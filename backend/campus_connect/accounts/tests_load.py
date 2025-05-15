from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, VerificationCode
from bloodbank.models import BloodGroup, Donor
import random
import time
from faker import Faker

class MultiUserLoadTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.faker = Faker()
        self.blood_group = BloodGroup.objects.create(name="A+")
        self.users = []
        self.donors = []
        self.num_users = 100
        self.num_donors = 50

    def create_user(self, index):
        """Helper to create and verify a user."""
        email = f"user{index}@example.com"
        user_data = {
            "name": self.faker.name(),
            "email": email,
            "password": "password123",
            "confirm_password": "password123",
            "blood_group": "A+"
        }
        # Register user
        response = self.client.post(reverse('register'), user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to register user {email}")
        user = User.objects.get(email=email)
        # Verify email
        code = VerificationCode.objects.get(user=user).code
        response = self.client.post(reverse('verify-email'), {"email": email, "code": code})
        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to verify user {email}")
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)
        return user

    def create_donor(self, user):
        """Helper to create a donor profile for a user."""
        self.client.force_authenticate(user=user)
        donor_data = {
            "emergency_contact": f"+1{self.faker.random_number(digits=10)}",
            "preferred_location": self.faker.city(),
            "last_donated": "2025-01-01",
            "consent": True
        }
        response = self.client.post(reverse('donor-register'), donor_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Failed to create donor for {user.email}")
        self.client.force_authenticate(user=None)
        return Donor.objects.get(user=user)

    def test_create_multiple_users(self):
        """Test creating and verifying 100 users."""
        start_time = time.time()
        for i in range(self.num_users):
            user = self.create_user(i)
            self.users.append(user)
        duration = time.time() - start_time
        print(f"Created {self.num_users} users in {duration:.2f} seconds")
        self.assertEqual(User.objects.count(), self.num_users, "Incorrect number of users created")

    def test_create_multiple_donors(self):
        """Test creating donor profiles for 50 users."""
        # Create users first
        for i in range(self.num_users):
            user = self.create_user(i)
            self.users.append(user)
        # Create donors for first 50 users
        start_time = time.time()
        for user in self.users[:self.num_donors]:
            donor = self.create_donor(user)
            self.donors.append(donor)
        duration = time.time() - start_time
        print(f"Created {self.num_donors} donors in {duration:.2f} seconds")
        self.assertEqual(Donor.objects.count(), self.num_donors, "Incorrect number of donors created")

    def test_user_list_pagination(self):
        """Test retrieving user list with pagination."""
        for i in range(self.num_users):
            user = self.create_user(i)
            self.users.append(user)
        start_time = time.time()
        response = self.client.get(reverse('user-list'), {"limit": 20, "offset": 0})
        duration = time.time() - start_time
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 20, "Incorrect number of users in paginated response")
        print(f"Retrieved user list (20 users) in {duration:.2f} seconds")

    def test_user_detail_retrieval(self):
        """Test retrieving individual user profiles."""
        for i in range(self.num_users):
            user = self.create_user(i)
            self.users.append(user)
        start_time = time.time()
        for user in random.sample(self.users, 10):  # Test 10 random users
            response = self.client.get(reverse('user-detail', args=[user.pk]))
            self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to retrieve user {user.email}")
            self.assertEqual(response.data["name"], user.name)
            self.assertNotIn("email", response.data, "Email should be hidden due to visibility settings")
        duration = time.time() - start_time
        print(f"Retrieved 10 user profiles in {duration:.2f} seconds")

    def test_donor_detail_retrieval(self):
        """Test retrieving individual donor profiles."""
        for i in range(self.num_users):
            user = self.create_user(i)
            self.users.append(user)
        for user in self.users[:self.num_donors]:
            donor = self.create_donor(user)
            self.donors.append(donor)
        start_time = time.time()
        for donor in random.sample(self.donors, 10):  # Test 10 random donors
            response = self.client.get(reverse('donor-detail', args=[donor.pk]))
            self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to retrieve donor {donor.user.email}")
            self.assertEqual(response.data["name"], donor.user.name)
        duration = time.time() - start_time
        print(f"Retrieved 10 donor profiles in {duration:.2f} seconds")

    def test_profile_updates(self):
        """Test updating user and donor profiles for multiple users."""
        # Create 10 fresh users to avoid interference
        users = []
        num_test_users = 10
        for i in range(num_test_users):
            user = self.create_user(i)
            users.append(user)
        # Create donors for first 5 users
        donors = []
        for user in users[:5]:
            donor = self.create_donor(user)
            donors.append(donor)
        
        start_time = time.time()
        updated_users = set()  # Track updated users to ensure uniqueness
        for user in random.sample(users, num_test_users):
            if user.pk in updated_users:
                continue  # Skip if already updated
            updated_users.add(user.pk)
            self.client.force_authenticate(user=user)
            # Reset name to original to avoid double updates
            original_name = self.faker.name()
            user.name = original_name
            user.save()
            # Update user profile
            new_name = f"Updated {original_name}"
            response = self.client.patch(reverse('user-profile'), {"name": new_name})
            self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to update user profile for {user.email}")
            self.assertEqual(response.data["data"]["name"], new_name, f"Name mismatch for {user.email}")
            # Update donor profile if exists
            if hasattr(user, 'donor_profile'):
                response = self.client.patch(reverse('donor-profile'), {"preferred_location": "Updated Location"})
                self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to update donor profile for {user.email}")
                self.assertEqual(response.data["data"]["preferred_location"], "Updated Location")
                # Test donor/profile/ endpoint
                response = self.client.patch(reverse('donor-profile-explicit'), {"preferred_location": "Updated Location 2"})
                self.assertEqual(response.status_code, status.HTTP_200_OK, f"Failed to update donor profile via /profile/ for {user.email}")
                self.assertEqual(response.data["data"]["preferred_location"], "Updated Location 2")
            self.client.force_authenticate(user=None)
        duration = time.time() - start_time
        print(f"Updated {len(updated_users)} user/donor profiles in {duration:.2f} seconds")
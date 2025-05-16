import factory
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from universities.models import University, AcademicUnit, TeacherDesignation
from accounts.models import User, VerificationCode, BloodGroup
from bloodbank.models import Donor
from lostandfound.models import LostItem, FoundItem, LostItemClaim, FoundItemClaim, ItemMedia
from rest_framework.authtoken.models import Token
from django.db.models.signals import post_save
from unittest.mock import patch
import os
import logging

logger = logging.getLogger(__name__)

# Factories
class UniversityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = University

    name = factory.Sequence(lambda n: f"University {n}")
    short_name = factory.Sequence(lambda n: f"U{n}")

class AcademicUnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AcademicUnit

    name = factory.Sequence(lambda n: f"Department {n}")
    short_name = factory.Sequence(lambda n: f"Dept{n}")
    unit_type = 'department'
    university = factory.SubFactory(UniversityFactory)

class TeacherDesignationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeacherDesignation

    name = factory.Sequence(lambda n: f"Professor {n}")

class BloodGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BloodGroup

    name = factory.Faker('word')

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker('name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    role = 'student'
    admin_level = 'none'
    university = factory.SubFactory(UniversityFactory)
    academic_unit = factory.SubFactory(AcademicUnitFactory, university=factory.SelfAttribute('..university'))
    is_active = True
    is_verified = True
    contact_visibility = 'email'

class DonorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Donor

    user = factory.SubFactory(UserFactory)
    emergency_contact = "+1234567890"
    preferred_location = "Campus Clinic"
    consent = True

class LostItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LostItem

    user = factory.SubFactory(UserFactory)
    university = factory.SubFactory(UniversityFactory)
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')
    lost_date = factory.LazyFunction(date.today)
    location = "Library"
    status = 'open'

class FoundItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FoundItem

    user = factory.SubFactory(UserFactory)
    university = factory.SubFactory(UniversityFactory)
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('paragraph')
    found_date = factory.LazyFunction(date.today)
    location = "Cafeteria"
    status = 'open'

class LostItemClaimFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LostItemClaim

    lost_item = factory.SubFactory(LostItemFactory)
    claimant = factory.SubFactory(UserFactory)
    description = factory.Faker('paragraph')

class FoundItemClaimFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FoundItemClaim

    found_item = factory.SubFactory(FoundItemFactory)
    claimant = factory.SubFactory(UserFactory)
    description = factory.Faker('paragraph')

class ItemMediaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItemMedia

    lost_item = factory.SubFactory(LostItemFactory)
    file = factory.django.FileField(filename='test.jpg')

# Base Test Case
class BaseAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.university = UniversityFactory()
        self.academic_unit = AcademicUnitFactory(university=self.university)
        self.blood_group = BloodGroupFactory(name="A+")
        # Users
        self.student = UserFactory(
            university=self.university,
            academic_unit=self.academic_unit,
            role='student',
            blood_group=self.blood_group
        )
        self.university_admin = UserFactory(
            university=self.university,
            academic_unit=self.academic_unit,
            role='student',
            admin_level='university'
        )
        self.app_admin = UserFactory(
            university=self.university,
            academic_unit=self.academic_unit,
            role='student',
            admin_level='app'
        )
        self.other_university = UniversityFactory()
        self.other_academic_unit = AcademicUnitFactory(university=self.other_university)
        self.other_university_admin = UserFactory(
            university=self.other_university,
            academic_unit=self.other_academic_unit,
            role='student',
            admin_level='university'
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def create_image(self):
        return SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

# Accounts App Tests
class AccountsTests(BaseAPITestCase):
    def test_register_success(self):
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': 'student',
            'university': self.university.id,
            'academic_unit': self.academic_unit.id,
            'blood_group': 'A+',
            'contact_visibility': 'email'
        }
        response = self.client.post('/api/accounts/register/', data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['message'], 'User registered, please verify your email.')
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        self.assertTrue(VerificationCode.objects.filter(user__email='test@example.com').exists())

    def test_register_duplicate_email(self):
        data = {
            'name': 'Test User',
            'email': self.student.email,
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': 'student',
            'university': self.university.id,
            'academic_unit': self.academic_unit.id
        }
        response = self.client.post('/api/accounts/register/', data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data['message'])

    def test_register_missing_academic_unit(self):
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123',
            'role': 'student',
            'university': self.university.id
        }
        response = self.client.post('/api/accounts/register/', data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('academic_unit', response.data['message'])

    def test_email_verification_success(self):
        user = UserFactory(is_active=False, is_verified=False)
        code = VerificationCode.objects.create(
            user=user,
            code='123456',
            purpose='email_verification',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        data = {'email': user.email, 'code': '123456'}
        response = self.client.post('/api/accounts/verify-email/', data)
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_verified)
        self.assertFalse(VerificationCode.objects.filter(id=code.id).exists())

    def test_email_verification_invalid_code(self):
        user = UserFactory(is_active=False, is_verified=False)
        VerificationCode.objects.create(
            user=user,
            code='123456',
            purpose='email_verification',
            expires_at=timezone.now() + timedelta(minutes=15)
        )
        data = {'email': user.email, 'code': 'wrong'}
        response = self.client.post('/api/accounts/verify-email/', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Invalid or expired code.')

    def test_login_success(self):
        data = {'email': self.student.email, 'password': 'testpass123'}
        response = self.client.post('/api/accounts/login/', data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['id'], self.student.id)

    def test_login_invalid_credentials(self):
        data = {'email': self.student.email, 'password': 'wrongpass'}
        response = self.client.post('/api/accounts/login/', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'Invalid credentials.')

    def test_logout_success(self):
        self.authenticate(self.student)
        Token.objects.create(user=self.student)
        response = self.client.post('/api/accounts/logout/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Logged out successfully.')
        self.assertFalse(Token.objects.filter(user=self.student).exists())

    def test_logout_unauthenticated(self):
        response = self.client.post('/api/accounts/logout/')
        self.assertEqual(response.status_code, 401)

    def test_user_list_authenticated(self):
        self.authenticate(self.student)
        response = self.client.get('/api/accounts/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) > 0)

    def test_user_list_unauthenticated(self):
        response = self.client.get('/api/accounts/')
        self.assertEqual(response.status_code, 401)

    def test_profile_get(self):
        self.authenticate(self.student)
        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.student.id)

    def test_profile_update(self):
        self.authenticate(self.student)
        data = {'name': 'Updated Name', 'contact_visibility': 'phone'}
        response = self.client.patch('/api/accounts/profile/', data)
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.name, 'Updated Name')
        self.assertEqual(self.student.contact_visibility, 'phone')

    def test_user_detail_anonymous(self):
        response = self.client.get(f'/api/accounts/{self.student.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.student.id)

    def test_user_detail_nonexistent(self):
        response = self.client.get('/api/accounts/999/')
        self.assertEqual(response.status_code, 404)

# Bloodbank App Tests
class BloodbankTests(BaseAPITestCase):
    def test_bloodgroup_list(self):
        response = self.client.get('/api/bloodbank/bloodgroups/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('A+', [item for item in response.data])

    def test_bloodgroup_detail(self):
        response = self.client.get('/api/bloodbank/bloodgroups/A+/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], 'A+')

    def test_bloodgroup_detail_nonexistent(self):
        response = self.client.get('/api/bloodbank/bloodgroups/X+/')
        self.assertEqual(response.status_code, 404)

    def test_donor_register_success(self):
        self.authenticate(self.student)
        data = {
            'emergency_contact': '+1234567890',
            'preferred_location': 'Clinic',
            'consent': True
        }
        response = self.client.post('/api/bloodbank/donor/register/', data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Donor.objects.filter(user=self.student).exists())

    def test_donor_register_already_registered(self):
        DonorFactory(user=self.student)
        self.authenticate(self.student)
        data = {
            'emergency_contact': '+1234567890',
            'preferred_location': 'Clinic',
            'consent': True
        }
        response = self.client.post('/api/bloodbank/donor/register/', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'User is already registered as a donor.')

    def test_donor_profile_get(self):
        donor = DonorFactory(user=self.student)
        self.authenticate(self.student)
        response = self.client.get('/api/bloodbank/donor/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user'], self.student.id)

    def test_donor_profile_get_non_donor(self):
        self.authenticate(self.student)
        response = self.client.get('/api/bloodbank/donor/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('No donor profile found', response.data['message'])

    def test_donor_profile_update(self):
        donor = DonorFactory(user=self.student)
        self.authenticate(self.student)
        data = {'preferred_location': 'Updated Clinic'}
        response = self.client.patch('/api/bloodbank/donor/', data)
        self.assertEqual(response.status_code, 200)
        donor.refresh_from_db()
        self.assertEqual(donor.preferred_location, 'Updated Clinic')

    def test_donor_withdraw(self):
        donor = DonorFactory(user=self.student)
        self.authenticate(self.student)
        response = self.client.post('/api/bloodbank/donor/withdraw/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Donor.objects.filter(user=self.student).exists())

    def test_donor_detail(self):
        donor = DonorFactory(user=self.student)
        response = self.client.get(f'/api/bloodbank/donor/{donor.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user'], self.student.id)

    def test_donor_list_filter(self):
        # Ensure user has the correct blood group
        self.student.blood_group = self.blood_group
        self.student.save()
        donor = DonorFactory(user=self.student, last_donated=date.today() - timedelta(days=1))
        print(f"Donors with blood_group=A+: {Donor.objects.filter(user__blood_group__name='A+').count()}")
        response = self.client.get(f'/api/bloodbank/donors/?blood_group=A+&last_donated_before={date.today().isoformat()}&limit=10')
        print(f"Donor list response: {response.data}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) > 0, f"Expected donors, got {response.data}")

# Universities App Tests
class UniversitiesTests(BaseAPITestCase):
    def test_university_list(self):
        response = self.client.get('/api/universities/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)

    def test_department_list(self):
        response = self.client.get('/api/universities/departments/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)

    def test_institute_list(self):
        AcademicUnitFactory(unit_type='institute')
        response = self.client.get('/api/universities/institutes/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)

    def test_teacher_designation_list(self):
        TeacherDesignationFactory()
        response = self.client.get('/api/universities/teacher-designations/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)

    def test_department_institute_list(self):
        response = self.client.get(f'/api/universities/departments-institutes/?name={self.university.short_name}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('departments', response.data)
        self.assertIn('institutes', response.data)

    def test_university_users(self):
        response = self.client.get(f'/api/universities/{self.university.short_name}/users/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('students', response.data)
        self.assertTrue(len(response.data['students']) > 0)

# Lost and Found App Tests
class LostAndFoundTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            name='Test User'
        )
        self.university = University.objects.create(name='Test University')
        self.client.force_authenticate(user=self.user)

    def test_lost_item_create(self):
        logger.info(f"Creating lost item as {self.user.email}")
        data = {
            'title': 'Lost Wallet',
            'description': 'Black leather wallet',
            'lost_date': date.today().isoformat(),
            'location': 'Library',
            'university': self.university.id
        }
        response = self.client.post('/api/lostandfound/lost/', data, format='json')
        self.assertEqual(response.status_code, 201, f"Expected 201, got {response.status_code}: {response.data}")
        lost_item = LostItem.objects.get(id=response.data['id'])
        self.assertEqual(lost_item.approval_status, 'pending', f"Expected approval_status='pending', got '{lost_item.approval_status}'")
        logger.info(f"Lost item created: {lost_item.title}, approval_status: {lost_item.approval_status}")

    @patch('lostandfound.models.post_save', autospec=True)  # Mock post_save signals
    def test_lost_item_create(self, mock_post_save):
        self.authenticate(self.student)
        data = {
            'title': 'Lost Wallet',
            'description': 'Black leather wallet',
            'lost_date': date.today().isoformat(),
            'location': 'Library',
            'university': self.university.id,
            'media_files': [self.create_image()]
        }
        response = self.client.post('/api/lostandfound/lost/', data, format='multipart')
        print(f"Created lost item approval_status: {LostItem.objects.last().approval_status}")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LostItem.objects.last().approval_status, 'pending')
        self.assertTrue(ItemMedia.objects.filter(lost_item__title='Lost Wallet').exists())

    def test_all_items_list(self):
        response = self.client.get('/api/lostandfound/all/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) >= 2, f"Expected at least 2 items, got {response.data['results']}")

    def test_pending_items_list_admin(self):
        self.authenticate(self.university_admin)
        response = self.client.get('/api/lostandfound/pending/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) >= 2)

    def test_pending_items_list_non_admin(self):
        self.authenticate(self.student)
        response = self.client.get('/api/lostandfound/pending/')
        self.assertEqual(response.status_code, 403)

    def test_lost_item_list(self):
        response = self.client.get('/api/lostandfound/lost/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) >= 1, f"Expected at least 1 lost item, got {response.data['results']}")

    def test_lost_item_create_invalid_date(self):
        self.authenticate(self.student)
        data = {
            'title': 'Lost Wallet',
            'description': 'Black leather wallet',
            'lost_date': (date.today() + timedelta(days=1)).isoformat(),
            'location': 'Library',
            'university': self.university.id
        }
        response = self.client.post('/api/lostandfound/lost/', data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('lost_date', response.data)

    def test_found_item_list(self):
        response = self.client.get('/api/lostandfound/found/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) >= 1, f"Expected at least 1 found item, got {response.data['results']}")

    def test_lost_item_detail(self):
        response = self.client.get(f'/api/lostandfound/lost/{self.lost_item.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.lost_item.id)

    def test_lost_item_detail_nonexistent(self):
        response = self.client.get('/api/lostandfound/lost/999/')
        self.assertEqual(response.status_code, 404)

    def test_lost_item_claim(self):
        other_user = UserFactory(university=self.university, academic_unit=self.academic_unit)
        self.authenticate(other_user)
        data = {
            'lost_item': self.lost_item.id,
            'description': 'I believe this is my wallet',
            'media_files': [self.create_image()]
        }
        print(f"Claiming lost_item ID: {self.lost_item.id}, exists: {LostItem.objects.filter(id=self.lost_item.id).exists()}")
        response = self.client.post('/api/lostandfound/lost/claim/', data, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(LostItemClaim.objects.filter(claimant=other_user).exists())

    def test_lost_item_claim_self(self):
        self.authenticate(self.student)
        data = {'lost_item': self.lost_item.id, 'description': 'My own item'}
        response = self.client.post('/api/lostandfound/lost/claim/', data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('You cannot claim your own lost item', str(response.data))

    def test_lost_item_resolve(self):
        claimant = UserFactory(university=self.university, academic_unit=self.academic_unit)
        LostItemClaimFactory(lost_item=self.lost_item, claimant=claimant)
        self.authenticate(self.student)
        data = {'status': 'found', 'resolved_by': claimant.id}
        response = self.client.post(f'/api/lostandfound/lost/{self.lost_item.id}/resolve/', data)
        self.assertEqual(response.status_code, 200)
        self.lost_item.refresh_from_db()
        self.assertEqual(self.lost_item.status, 'found')
        self.assertEqual(self.lost_item.resolved_by, claimant)

    def test_lost_item_approve(self):
        self.authenticate(self.university_admin)
        data = {'approval_status': 'approved'}
        response = self.client.post(f'/api/lostandfound/lost/{self.lost_item_pending.id}/approve/', data)
        self.assertEqual(response.status_code, 200)
        self.lost_item_pending.refresh_from_db()
        self.assertEqual(self.lost_item_pending.approval_status, 'approved')

    def test_lost_item_approve_unauthorized(self):
        self.authenticate(self.other_university_admin)
        data = {'approval_status': 'approved'}
        response = self.client.post(f'/api/lostandfound/lost/{self.lost_item_pending.id}/approve/', data)
        self.assertEqual(response.status_code, 403)

    def test_resolved_items_list(self):
        response = self.client.get('/api/lostandfound/resolved/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) >= 2, f"Expected at least 2 resolved items, got {response.data['results']}")

    def test_my_claims_list(self):
        LostItemClaimFactory(claimant=self.student)
        self.authenticate(self.student)
        response = self.client.get('/api/lostandfound/my-claims/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) >= 1)

    def test_my_posts_list(self):
        self.authenticate(self.student)
        response = self.client.get('/api/lostandfound/my-posts/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) >= 2)

    def test_lost_item_claims_list_owner(self):
        claim = LostItemClaimFactory(lost_item=self.lost_item, claimant=UserFactory(university=self.university, academic_unit=self.academic_unit))
        self.authenticate(self.student)
        response = self.client.get(f'/api/lostandfound/lost/{self.lost_item.id}/claims/')
        print(f"Checking claims for lost_item ID: {self.lost_item.id}, user: {self.student.email}, claim_lost_item_user: {claim.lost_item.user.email}, exists: {LostItem.objects.filter(id=self.lost_item.id).exists()}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data['results']) >= 1)

    def test_history(self):
        LostItemClaimFactory(claimant=self.student)
        self.authenticate(self.student)
        response = self.client.get('/api/lostandfound/history/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('posts', response.data)
        self.assertIn('claims_made', response.data)
        self.assertIn('claims_received', response.data)

    def test_media_access_owner(self):
        media = ItemMediaFactory(lost_item=self.lost_item)
        self.authenticate(self.student)
        response = self.client.get(f'/api/lostandfound/media/{media.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_media_access_unauthorized(self):
        media = ItemMediaFactory(lost_item=self.lost_item)
        other_user = UserFactory(university=self.university, academic_unit=self.academic_unit)
        self.authenticate(other_user)
        response = self.client.get(f'/api/lostandfound/media/{media.id}/')
        self.assertEqual(response.status_code, 403)
import factory
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from universities.models import University
from .models import LostItem, FoundItem, LostItemClaim, FoundItemClaim, ItemMedia
from django.utils import timezone
from datetime import date, time
import os
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

# Factories
class UniversityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = University

    name = factory.Sequence(lambda n: f"University {n}")

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker('name')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    admin_level = None
    university = factory.SubFactory(UniversityFactory)

class LostItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LostItem

    user = factory.SubFactory(UserFactory)
    university = factory.SubFactory(UniversityFactory)
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text')
    lost_date = date.today()
    approximate_time = time(14, 30)
    location = "Library"
    status = 'open'
    approval_status = 'pending'

class FoundItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FoundItem

    user = factory.SubFactory(UserFactory)
    university = factory.SubFactory(UniversityFactory)
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text')
    found_date = date.today()
    approximate_time = time(14, 30)
    location = "Cafeteria"
    status = 'open'
    approval_status = 'pending'

class LostItemClaimFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LostItemClaim

    lost_item = factory.SubFactory(LostItemFactory, approval_status='approved', status='open')
    claimant = factory.SubFactory(UserFactory)
    description = factory.Faker('text')

class FoundItemClaimFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FoundItemClaim

    found_item = factory.SubFactory(FoundItemFactory, approval_status='approved', status='open')
    claimant = factory.SubFactory(UserFactory)
    description = factory.Faker('text')

class ItemMediaFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ItemMedia

    lost_item = factory.SubFactory(LostItemFactory)
    file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
    uploaded_at = factory.LazyFunction(timezone.now)

class LostAndFoundAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.university = UniversityFactory()
        # Users
        self.user = UserFactory(university=self.university)
        self.other_user = UserFactory(university=self.university)
        self.university_admin = UserFactory(university=self.university, admin_level='university')
        self.app_admin = UserFactory(university=self.university, admin_level='app')
        self.other_university = UniversityFactory()
        self.other_university_admin = UserFactory(university=self.other_university, admin_level='university')
        # Lost and Found Items
        self.lost_item = LostItemFactory(user=self.user, university=self.university, approval_status='approved', status='open')
        self.found_item = FoundItemFactory(user=self.user, university=self.university, approval_status='approved', status='open')
        self.pending_lost_item = LostItemFactory(user=self.user, university=self.university, approval_status='pending')
        self.resolved_lost_item = LostItemFactory(user=self.user, university=self.university, approval_status='approved', status='found')
        self.resolved_found_item = FoundItemFactory(user=self.user, university=self.university, approval_status='approved', status='returned')
        self.other_user_lost_item = LostItemFactory(user=self.other_user, university=self.university, approval_status='approved', status='open')
        # Claims
        self.lost_claim = LostItemClaimFactory(lost_item=self.lost_item, claimant=self.other_user)
        self.found_claim = FoundItemClaimFactory(found_item=self.found_item, claimant=self.other_user)
        # Media
        self.lost_item_media = ItemMediaFactory(lost_item=self.lost_item)
        self.found_item_media = ItemMediaFactory(found_item=self.found_item)
        self.lost_claim_media = ItemMediaFactory(lost_item=None, lost_item_claim=self.lost_claim)
        self.found_claim_media = ItemMediaFactory(found_item=None, found_item_claim=self.found_claim)

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_all_items_list(self):
        response = self.client.get('/api/lostandfound/all/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 2)  # lost_item, found_item
        self.assertTrue(all(item['approval_status'] == 'approved' and item['status'] in ['open', 'claimed'] for item in data))
        self.assertTrue(all('post_type' in item and 'claims_url' in item and 'detail_url' in item for item in data))

    def test_all_items_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/lostandfound/all/')
        self.assertEqual(response.status_code, 200)  # AllowAny permission

    def test_pending_items_admin(self):
        self.authenticate(self.university_admin)
        response = self.client.get('/api/lostandfound/pending/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 1)  # pending_lost_item
        self.assertTrue(all(item['approval_status'] == 'pending' for item in data))
        self.assertTrue(all('approve_url' in item and item['approve_url'] for item in data))

    def test_pending_items_non_admin(self):
        self.authenticate(self.user)
        response = self.client.get('/api/lostandfound/pending/')
        self.assertEqual(response.status_code, 403)

    def test_pending_items_app_admin(self):
        self.authenticate(self.app_admin)
        response = self.client.get('/api/lostandfound/pending/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 1)  # pending_lost_item

    def test_pending_items_other_university_admin(self):
        self.authenticate(self.other_university_admin)
        response = self.client.get('/api/lostandfound/pending/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 0)  # No pending items in other university

    def test_resolved_items_list(self):
        response = self.client.get('/api/lostandfound/resolved/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 2)  # resolved_lost_item, resolved_found_item
        self.assertTrue(all(item['approval_status'] == 'approved' for item in data))
        self.assertTrue(all(item['status'] in ['found', 'returned'] for item in data))

    def test_lost_item_list(self):
        self.authenticate(self.user)
        response = self.client.get('/api/lostandfound/lost/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 3)  # lost_item, pending_lost_item, resolved_lost_item (owner sees all)
        self.assertTrue(all(item['post_type'] == 'lost' for item in data))

    def test_lost_item_list_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/lostandfound/lost/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 2)  # lost_item, other_user_lost_item (only approved, unresolved)

    def test_lost_item_create_valid(self):
        self.authenticate(self.user)
        data = {
            'title': 'Lost Wallet',
            'description': 'Black leather wallet',
            'lost_date': '2025-05-15',
            'approximate_time': '14:30:00',
            'location': 'Library',
            'university': self.university.id,
            'media_files': [SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")]
        }
        response = self.client.post('/api/lostandfound/lost/', data, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LostItem.objects.count(), 5)
        self.assertEqual(ItemMedia.objects.filter(lost_item__title='Lost Wallet').count(), 1)
        self.assertEqual(response.json()['approval_status'], 'pending')

    def test_lost_item_create_future_date(self):
        self.authenticate(self.user)
        data = {
            'title': 'Lost Wallet',
            'description': 'Black leather wallet',
            'lost_date': '2025-05-17',  # Future date
            'approximate_time': '14:30:00',
            'location': 'Library',
            'university': self.university.id
        }
        response = self.client.post('/api/lostandfound/lost/', data, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertIn('lost_date', response.json()['error'])

    def test_lost_item_create_unauthenticated(self):
        self.client.force_authenticate(user=None)
        data = {
            'title': 'Lost Wallet',
            'description': 'Black leather wallet',
            'lost_date': '2025-05-15',
            'location': 'Library',
            'university': self.university.id
        }
        response = self.client.post('/api/lostandfound/lost/', data, format='multipart')
        self.assertEqual(response.status_code, 401)

    def test_found_item_create_valid(self):
        self.authenticate(self.user)
        data = {
            'title': 'Found Keys',
            'description': 'Car keys with red tag',
            'found_date': '2025-05-15',
            'approximate_time': '14:30:00',
            'location': 'Cafeteria',
            'university': self.university.id
        }
        response = self.client.post('/api/lostandfound/found/', data, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FoundItem.objects.count(), 4)
        self.assertEqual(response.json()['approval_status'], 'pending')

    def test_lost_item_detail(self):
        response = self.client.get(f'/api/lostandfound/lost/{self.lost_item.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['id'], self.lost_item.id)
        self.assertEqual(data['post_type'], 'lost')
        self.assertTrue('claims_url' in data)

    def test_lost_item_detail_not_found(self):
        response = self.client.get('/api/lostandfound/lost/999/')
        self.assertEqual(response.status_code, 404)

    def test_lost_item_detail_resolved(self):
        response = self.client.get(f'/api/lostandfound/lost/{self.resolved_lost_item.id}/')
        self.assertEqual(response.status_code, 404)  # Resolved items not accessible

    def test_lost_item_claim_valid(self):
        self.authenticate(self.other_user)
        data = {
            'lost_item': self.lost_item.id,
            'description': 'This is my wallet',
            'media_files': [SimpleUploadedFile("proof.jpg", b"file_content", content_type="image/jpeg")]
        }
        response = self.client.post('/api/lostandfound/lost/claim/', data, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LostItemClaim.objects.count(), 2)
        self.assertEqual(ItemMedia.objects.filter(lost_item_claim__lost_item=self.lost_item).count(), 1)

    def test_lost_item_claim_self(self):
        self.authenticate(self.user)
        data = {
            'lost_item': self.lost_item.id,
            'description': 'This is my wallet'
        }
        response = self.client.post('/api/lostandfound/lost/claim/', data, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertIn('You cannot claim your own lost item', str(response.json()))

    def test_lost_item_claim_duplicate(self):
        self.authenticate(self.other_user)
        data = {
            'lost_item': self.lost_item.id,
            'description': 'This is my wallet again'
        }
        response = self.client.post('/api/lostandfound/lost/claim/', data, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertIn('You have already claimed this item', str(response.json()))

    def test_lost_item_claim_unauthenticated(self):
        self.client.force_authenticate(user=None)
        data = {
            'lost_item': self.lost_item.id,
            'description': 'This is my wallet'
        }
        response = self.client.post('/api/lostandfound/lost/claim/', data, format='multipart')
        self.assertEqual(response.status_code, 401)

    def test_lost_item_resolve_owner(self):
        self.authenticate(self.user)
        data = {
            'status': 'found',
            'resolved_by': self.other_user.id
        }
        response = self.client.post(f'/api/lostandfound/lost/{self.lost_item.id}/resolve/', data)
        self.assertEqual(response.status_code, 200)
        self.lost_item.refresh_from_db()
        self.assertEqual(self.lost_item.status, 'found')
        self.assertEqual(self.lost_item.resolved_by, self.other_user)

    def test_lost_item_resolve_non_owner(self):
        self.authenticate(self.other_user)
        data = {
            'status': 'found',
            'resolved_by': self.other_user.id
        }
        response = self.client.post(f'/api/lostandfound/lost/{self.lost_item.id}/resolve/', data)
        self.assertEqual(response.status_code, 403)

    def test_lost_item_resolve_invalid_claimant(self):
        self.authenticate(self.user)
        data = {
            'status': 'found',
            'resolved_by': self.user.id  # Not a claimant
        }
        response = self.client.post(f'/api/lostandfound/lost/{self.lost_item.id}/resolve/', data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Resolved_by must be one of the claimants', str(response.json()))

    def test_lost_item_approve_admin(self):
        self.authenticate(self.university_admin)
        data = {'approval_status': 'approved'}
        response = self.client.post(f'/api/lostandfound/lost/{self.pending_lost_item.id}/approve/', data)
        self.assertEqual(response.status_code, 200)
        self.pending_lost_item.refresh_from_db()
        self.assertEqual(self.pending_lost_item.approval_status, 'approved')

    def test_lost_item_approve_non_admin(self):
        self.authenticate(self.user)
        data = {'approval_status': 'approved'}
        response = self.client.post(f'/api/lostandfound/lost/{self.pending_lost_item.id}/approve/', data)
        self.assertEqual(response.status_code, 403)

    def test_lost_item_approve_other_university(self):
        self.authenticate(self.other_university_admin)
        data = {'approval_status': 'approved'}
        response = self.client.post(f'/api/lostandfound/lost/{self.pending_lost_item.id}/approve/', data)
        self.assertEqual(response.status_code, 403)

    def test_my_posts(self):
        self.authenticate(self.user)
        response = self.client.get('/api/lostandfound/my-posts/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 4)  # lost_item, found_item, pending_lost_item, resolved_lost_item
        self.assertTrue(all('claims_url' in item and 'resolve_url' in item for item in data))
        self.assertTrue(all(item['resolve_url'] for item in data))  # Owner has resolve_url
        self.assertTrue(all(item['approve_url'] is None for item in data))  # Non-admin

    def test_my_posts_admin(self):
        self.authenticate(self.university_admin)
        LostItemFactory(user=self.university_admin, university=self.university)
        response = self.client.get('/api/lostandfound/my-posts/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertTrue(all(item['approve_url'] for item in data))  # Admin has approve_url

    def test_my_posts_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/lostandfound/my-posts/')
        self.assertEqual(response.status_code, 401)

    def test_my_claims(self):
        self.authenticate(self.other_user)
        response = self.client.get('/api/lostandfound/my-claims/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 2)  # lost_claim, found_claim

    def test_lost_item_claims_owner(self):
        self.authenticate(self.user)
        response = self.client.get(f'/api/lostandfound/lost/{self.lost_item.id}/claims/')
        self.assertEqual(response.status_code, 200)
        data = response.json()['results']
        self.assertEqual(len(data), 1)  # lost_claim

    def test_lost_item_claims_non_owner(self):
        self.authenticate(self.other_user)
        response = self.client.get(f'/api/lostandfound/lost/{self.lost_item.id}/claims/')
        self.assertEqual(response.status_code, 403)

    def test_lost_item_claims_admin(self):
        self.authenticate(self.university_admin)
        response = self.client.get(f'/api/lostandfound/lost/{self.lost_item.id}/claims/')
        self.assertEqual(response.status_code, 200)

    def test_history(self):
        self.authenticate(self.user)
        response = self.client.get('/api/lostandfound/history/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['posts']), 4)  # All user posts
        self.assertEqual(len(data['claims_made']), 0)  # No claims made by user
        self.assertEqual(len(data['claims_received']), 2)  # lost_claim, found_claim

    def test_media_access_owner(self):
        self.authenticate(self.user)
        response = self.client.get(f'/api/lostandfound/media/{self.lost_item_media.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/jpeg')

    def test_media_access_claimant(self):
        self.authenticate(self.other_user)
        response = self.client.get(f'/api/lostandfound/media/{self.lost_item_media.id}/')
        self.assertEqual(response.status_code, 200)  # Claimant has access

    def test_media_access_non_authorized(self):
        self.authenticate(self.other_university_admin)
        response = self.client.get(f'/api/lostandfound/media/{self.lost_item_media.id}/')
        self.assertEqual(response.status_code, 403)

    def test_media_access_not_found(self):
        self.authenticate(self.user)
        response = self.client.get('/api/lostandfound/media/invalid_id/')
        self.assertEqual(response.status_code, 404)

    def test_pagination(self):
        self.authenticate(self.user)
        for _ in range(10):
            LostItemFactory(user=self.user, university=self.university, approval_status='approved', status='open')
        response = self.client.get('/api/lostandfound/my-posts/?limit=5')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 5)
        self.assertTrue('next' in data)
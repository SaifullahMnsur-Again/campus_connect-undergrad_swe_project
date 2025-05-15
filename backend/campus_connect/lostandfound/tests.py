from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User
from universities.models import University
from bloodbank.models import BloodGroup
from rest_framework.authtoken.models import Token
from lostandfound.models import LostItem, FoundItem, LostItemClaim, FoundItemClaim, ItemMedia
from datetime import date, time, datetime
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import os

class LostAndFoundAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.blood_group = BloodGroup.objects.create(name="A+")
        self.university = University.objects.create(name="University of Dhaka")
        
        # Create users
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
        
        # Create tokens
        self.token = Token.objects.create(user=self.user)
        self.other_token = Token.objects.create(user=self.other_user)
        
        # Sample data for POST requests
        self.lost_item_data = {
            "university": self.university.id,
            "title": "Lost Wallet",
            "description": "Black leather wallet with ID cards",
            "lost_date": "2025-05-01",
            "approximate_time": "14:30",
            "location": "Library"
        }
        self.found_item_data = {
            "university": self.university.id,
            "title": "Found Keys",
            "description": "Set of house keys with a blue keychain",
            "found_date": "2025-05-01",
            "approximate_time": "15:00",
            "location": "Cafeteria"
        }
        
        # Sample media file
        self.image_file = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        self.video_file = SimpleUploadedFile(
            "test_video.mp4",
            b"video_content",
            content_type="video/mp4"
        )

    def test_list_all_items(self):
        # Create sample items with distinct created_at
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            approximate_time=time(14, 30),
            location="Library",
            status="open",
            created_at=timezone.now()
        )
        found_item = FoundItem.objects.create(
            user=self.other_user,
            university=self.university,
            title="Found Keys",
            description="House keys",
            found_date=date(2025, 5, 1),
            approximate_time=time(15, 0),
            location="Cafeteria",
            status="open",
            created_at=timezone.now() - timezone.timedelta(seconds=1)
        )
        
        response = self.client.get(reverse('all-items-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        # Check for either lost_date or found_date
        self.assertTrue(
            'lost_date' in response.data['results'][0] or 'found_date' in response.data['results'][0]
        )
        self.assertTrue(
            'lost_date' in response.data['results'][1] or 'found_date' in response.data['results'][1]
        )

    def test_list_all_items_pagination(self):
        for i in range(25):
            LostItem.objects.create(
                user=self.user,
                university=self.university,
                title=f"Lost Item {i}",
                description="Test item",
                lost_date=date(2025, 5, 1),
                location="Library",
                status="open",
                created_at=timezone.now() - timezone.timedelta(seconds=i)
            )
        
        response = self.client.get(reverse('all-items-list'), {'limit': 10, 'offset': 20})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNone(response.data['next'])  # Only 25 items, so offset=20 covers the last 5

    def test_create_lost_item_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = self.lost_item_data.copy()
        data['media_files'] = [self.image_file]
        response = self.client.post(reverse('lost-item-list'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Lost Wallet")
        self.assertEqual(response.data['approximate_time'], "14:30:00")
        self.assertEqual(response.data['user']['id'], self.user.id)
        self.assertEqual(len(response.data['media']), 1)
        self.assertEqual(len(response.data['media'][0]['id']), 16)
        self.assertTrue(response.data['media'][0]['file_url'].endswith(f"/api/lostandfound/media/{response.data['media'][0]['id']}/"))

    def test_create_lost_item_without_approximate_time(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = self.lost_item_data.copy()
        del data['approximate_time']
        response = self.client.post(reverse('lost-item-list'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['approximate_time'])

    def test_create_lost_item_unauthenticated(self):
        response = self.client.post(reverse('lost-item-list'), self.lost_item_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_lost_item_invalid_date(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = self.lost_item_data.copy()
        data['lost_date'] = "2025-12-01"  # Future date
        response = self.client.post(reverse('lost-item-list'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('lost_date', response.data)

    def test_create_lost_item_invalid_time(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = self.lost_item_data.copy()
        data['approximate_time'] = "25:00"  # Invalid time
        response = self.client.post(reverse('lost-item-list'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('approximate_time', response.data)

    def test_list_lost_items(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            approximate_time=time(14, 30),
            location="Library",
            status="open"
        )
        response = self.client.get(reverse('lost-item-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        result = response.data['results'][0]
        self.assertEqual(result['title'], "Lost Wallet")
        self.assertEqual(result['approximate_time'], "14:30:00")
        self.assertEqual(
            set(result.keys()),
            {'id', 'user', 'title', 'description', 'lost_date', 'approximate_time',
             'location', 'status', 'created_at', 'media', 'detail_url'}
        )
        self.assertEqual(set(result['user'].keys()), {'id', 'name', 'detail_url'})
        self.assertTrue(result['detail_url'].endswith(f"/api/lostandfound/lost/{result['id']}/"))
        self.assertTrue(result['user']['detail_url'].endswith(f"/api/accounts/{result['user']['id']}/"))

    def test_retrieve_lost_item(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            approximate_time=time(14, 30),
            location="Library",
            status="open"
        )
        response = self.client.get(reverse('lost-item-detail', kwargs={'pk': lost_item.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Lost Wallet")
        self.assertEqual(response.data['approximate_time'], "14:30:00")

    def test_retrieve_lost_item_not_found(self):
        response = self.client.get(reverse('lost-item-detail', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_found_item_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = self.found_item_data.copy()
        data['media_files'] = [self.video_file]
        response = self.client.post(reverse('found-item-list'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Found Keys")
        self.assertEqual(response.data['approximate_time'], "15:00:00")
        self.assertEqual(len(response.data['media']), 1)
        self.assertEqual(len(response.data['media'][0]['id']), 16)

    def test_create_found_item_unauthenticated(self):
        response = self.client.post(reverse('found-item-list'), self.found_item_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_found_items(self):
        FoundItem.objects.create(
            user=self.user,
            university=self.university,
            title="Found Keys",
            description="House keys",
            found_date=date(2025, 5, 1),
            approximate_time=time(15, 0),
            location="Cafeteria",
            status="open"
        )
        response = self.client.get(reverse('found-item-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], "Found Keys")

    def test_retrieve_found_item(self):
        found_item = FoundItem.objects.create(
            user=self.user,
            university=self.university,
            title="Found Keys",
            description="House keys",
            found_date=date(2025, 5, 1),
            approximate_time=time(15, 0),
            location="Cafeteria",
            status="open"
        )
        response = self.client.get(reverse('found-item-detail', kwargs={'pk': found_item.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Found Keys")

    def test_retrieve_found_item_not_found(self):
        response = self.client.get(reverse('found-item-detail', kwargs={'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_claim_lost_item(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="open"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        data = {
            "lost_item": lost_item.id,
            "description": "I think this is my wallet",
            "media_files": [self.image_file]
        }
        response = self.client.post(reverse('lost-item-claim'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['claimant']['id'], self.other_user.id)
        self.assertEqual(len(response.data['media']), 1)
        lost_item.refresh_from_db()
        self.assertEqual(lost_item.status, "claimed")

    def test_claim_lost_item_own_item(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="open"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            "lost_item": lost_item.id,
            "description": "My own wallet"
        }
        response = self.client.post(reverse('lost-item-claim'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot claim your own", str(response.data).lower())

    def test_claim_lost_item_not_open(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="found"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        data = {
            "lost_item": lost_item.id,
            "description": "I think this is my wallet"
        }
        response = self.client.post(reverse('lost-item-claim'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not open for claims", str(response.data).lower())

    def test_claim_found_item(self):
        found_item = FoundItem.objects.create(
            user=self.user,
            university=self.university,
            title="Found Keys",
            description="House keys",
            found_date=date(2025, 5, 1),
            location="Cafeteria",
            status="open"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        data = {
            "found_item": found_item.id,
            "description": "These are my keys"
        }
        response = self.client.post(reverse('found-item-claim'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        found_item.refresh_from_db()
        self.assertEqual(found_item.status, "claimed")

    def test_resolve_lost_item_found(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="claimed"
        )
        LostItemClaim.objects.create(
            lost_item=lost_item,
            claimant=self.other_user,
            description="I found it"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            "status": "found",
            "resolved_by": self.other_user.id
        }
        response = self.client.post(reverse('lost-item-resolve', kwargs={'pk': lost_item.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lost_item.refresh_from_db()
        self.assertEqual(lost_item.status, "found")
        self.assertEqual(lost_item.resolved_by, self.other_user)

    def test_resolve_lost_item_externally_found(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="open"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            "status": "externally_found"
        }
        response = self.client.post(reverse('lost-item-resolve', kwargs={'pk': lost_item.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lost_item.refresh_from_db()
        self.assertEqual(lost_item.status, "externally_found")
        self.assertIsNone(lost_item.resolved_by)

    def test_resolve_lost_item_unauthorized(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="open"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        data = {
            "status": "found",
            "resolved_by": self.other_user.id
        }
        response = self.client.post(reverse('lost-item-resolve', kwargs={'pk': lost_item.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_resolve_lost_item_invalid_claimant(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="claimed"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            "status": "found",
            "resolved_by": self.other_user.id
        }
        response = self.client.post(reverse('lost-item-resolve', kwargs={'pk': lost_item.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("must be one of the claimants", str(response.data).lower())

    def test_resolve_found_item_returned(self):
        found_item = FoundItem.objects.create(
            user=self.user,
            university=self.university,
            title="Found Keys",
            description="House keys",
            found_date=date(2025, 5, 1),
            location="Cafeteria",
            status="claimed"
        )
        FoundItemClaim.objects.create(
            found_item=found_item,
            claimant=self.other_user,
            description="My keys"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        data = {
            "status": "returned",
            "resolved_by": self.other_user.id
        }
        response = self.client.post(reverse('found-item-resolve', kwargs={'pk': found_item.id}), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        found_item.refresh_from_db()
        self.assertEqual(found_item.status, "returned")

    def test_list_resolved_items(self):
        LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="found"
        )
        FoundItem.objects.create(
            user=self.user,
            university=self.university,
            title="Found Keys",
            description="House keys",
            found_date=date(2025, 5, 1),
            location="Cafeteria",
            status="returned"
        )
        response = self.client.get(reverse('resolved-items-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_access_media_authorized(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="open"
        )
        media = ItemMedia.objects.create(lost_item=lost_item, file=self.image_file)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('media-access', kwargs={'pk': media.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers['Content-Type'], 'image/jpeg')

    def test_access_media_by_claimant(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="claimed"
        )
        media = ItemMedia.objects.create(lost_item=lost_item, file=self.image_file)
        LostItemClaim.objects.create(
            lost_item=lost_item,
            claimant=self.other_user,
            description="I found it"
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        response = self.client.get(reverse('media-access', kwargs={'pk': media.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_media_unauthorized(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="open"
        )
        media = ItemMedia.objects.create(lost_item=lost_item, file=self.image_file)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.other_token.key}')
        response = self.client.get(reverse('media-access', kwargs={'pk': media.id}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_access_media_not_found(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('media-access', kwargs={'pk': 'nonexistent12345678'}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_access_media_missing_file(self):
        lost_item = LostItem.objects.create(
            user=self.user,
            university=self.university,
            title="Lost Wallet",
            description="Black leather wallet",
            lost_date=date(2025, 5, 1),
            location="Library",
            status="open"
        )
        media = ItemMedia.objects.create(lost_item=lost_item, file=self.image_file)
        os.remove(media.file.path)  # Simulate missing file
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(reverse('media-access', kwargs={'pk': media.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
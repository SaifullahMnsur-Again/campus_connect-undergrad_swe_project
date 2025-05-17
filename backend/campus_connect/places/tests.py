from rest_framework.test import APITestCase
from django.urls import reverse
from .models import Place, PlaceType
from universities.models import University
from accounts.models import User

class PlaceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='test@example.com', name='Test User', password='password')
        self.university = University.objects.create(name='Test University', short_name='TU')
        self.place_type = PlaceType.objects.create(name='building')
        self.campus = Place.objects.create(
            name='Campus', university=self.university, place_type=self.place_type,
            created_by=self.user, approval_status='approved'
        )
        self.building = Place.objects.create(
            name='Building', university=self.university, place_type=self.place_type,
            parent=self.campus, created_by=self.user, approval_status='approved'
        )

    def test_cannot_delete_place_with_children(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(reverse('places:place-delete', kwargs={'pk': self.campus.pk}))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], "Cannot delete place with child places. Delete all child places first or use recursive deletion.")

    def test_recursive_delete(self):
        self.client.force_authenticate(user=self.user)
        self.user.admin_level = 'app'
        self.user.save()
        response = self.client.delete(reverse('places:place-recursive-delete', kwargs={'pk': self.campus.pk}))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Place.objects.filter(pk=self.campus.pk).exists())
        self.assertFalse(Place.objects.filter(pk=self.building.pk).exists())
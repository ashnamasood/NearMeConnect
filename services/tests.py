# services/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from .models import ServiceCategory  # Add this import

class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='test')
        self.client.force_authenticate(user=self.user)
        
        # Create a test service category
        ServiceCategory.objects.create(name='electrician')

    def test_provider_list(self):
        response = self.client.get('/api/providers/')
        self.assertEqual(response.status_code, 200)
        
    def test_service_discovery(self):
        response = self.client.get('/api/discover/?service=electrician')
        self.assertEqual(response.status_code, 200)
        self.assertIn('local_providers', response.data)
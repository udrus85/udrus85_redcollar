from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Point, Message

# Create your tests here.

class PointModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_point_creation(self):
        point = Point.objects.create(user=self.user, name='Test Point', location='POINT(0 0)')
        self.assertEqual(point.name, 'Test Point')

class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.point = Point.objects.create(user=self.user, name='Test Point', location='POINT(0 0)')

    def test_message_creation(self):
        message = Message.objects.create(user=self.user, point=self.point, content='Test message')
        self.assertEqual(message.content, 'Test message')

class PointAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_create_point(self):
        url = reverse('point-list')
        data = {'name': 'New Point', 'location': {'type': 'Point', 'coordinates': [0, 0]}}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

class MessageAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.point = Point.objects.create(user=self.user, name='Test Point', location='POINT(0 0)')
        self.client.force_authenticate(user=self.user)

    def test_create_message(self):
        url = reverse('message-list')
        data = {'point': self.point.id, 'content': 'New message'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

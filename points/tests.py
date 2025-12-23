from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Message, Point


class PointModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')

    def test_point_creation(self):
        point = Point.objects.create(user=self.user, name='Test Point', description='desc', latitude=0, longitude=0)
        self.assertEqual(point.name, 'Test Point')
        self.assertEqual(point.latitude, 0)


class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.point = Point.objects.create(user=self.user, name='Test Point', description='desc', latitude=0, longitude=0)

    def test_message_creation(self):
        message = Message.objects.create(user=self.user, point=self.point, content='Test message')
        self.assertEqual(message.content, 'Test message')
        self.assertEqual(message.point, self.point)


class PointAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_create_point(self):
        url = reverse('points-list')
        data = {'name': 'New Point', 'description': 'desc', 'latitude': 0, 'longitude': 0}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Point.objects.count(), 1)

    def test_search_points(self):
        Point.objects.create(user=self.user, name='Nearby', description='', latitude=0, longitude=0)
        url = reverse('points-search') + '?latitude=0&longitude=0&radius=5'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class MessageAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.point = Point.objects.create(user=self.user, name='Test Point', description='', latitude=0, longitude=0)
        self.client.force_authenticate(user=self.user)

    def test_create_message(self):
        url = reverse('messages-list')
        data = {'point': self.point.id, 'content': 'New message'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Message.objects.count(), 1)

    def test_search_messages(self):
        Message.objects.create(user=self.user, point=self.point, content='Hi')
        url = reverse('messages-search') + '?latitude=0&longitude=0&radius=5'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

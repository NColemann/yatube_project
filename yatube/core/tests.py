from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class CoreURLTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.guest_client = Client()

    def test_unexisting_url(self):
        """Неизвестный URL."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

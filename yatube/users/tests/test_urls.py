from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_url_uses_anonymous_user(self):
        """URL-адрес доступен пользователю."""
        urls_check = [
            '/auth/signup/',
            '/auth/login/',
            '/auth/auth/logout/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/auth/reset/done/',
        ]
        for address in urls_check:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_authorized(self):
        """URL-адрес доступен авторизованному пользователю."""
        urls_check = [
            '/auth/password_change/',
            '/auth/password_change/done/',
        ]
        for address in urls_check:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

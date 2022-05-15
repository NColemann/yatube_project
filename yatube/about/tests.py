from django.urls import reverse
from http import HTTPStatus

from django.test import TestCase, Client


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_pages_uses_correct_template(self):
        """URL-адрес доступен и использует соответствующий шаблон."""
        templates_pages_names = (
            ('about/author.html', reverse('about:author')),
            ('about/tech.html', reverse('about:tech')),
        )
        for template, url in templates_pages_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

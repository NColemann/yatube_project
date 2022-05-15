from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user_other = User.objects.create_user(username='another')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user_other)
        cache.clear()

    def test_url_uses_anonymous_user(self):
        """URL-адрес доступен пользователю."""
        urls_check = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ),
            reverse(
                'posts:profile',
                kwargs={'username': 'HasNoName'},
            ),
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk},
            ),
        )
        for url in urls_check:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_authorized(self):
        """URL-адрес доступен авторизованному пользователю."""
        urls_check = (
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ),
        )
        for url in urls_check:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_anonymous_user(self):
        """Проверяем редиректы для неавторизованного пользователя."""
        urls_for_redirect = (
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ),
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk},
            ),
        )
        for url in urls_for_redirect:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_url_redirect_another_user(self):
        """Страница /posts/<post_id>/edit/ перенаправляет
        авторизованного пользователя не автора поста."""
        response = self.authorized_client2.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ),
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk},
        ))

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = (
            (reverse('posts:index'), 'posts/index.html'),
            (reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ), 'posts/group_list.html'),
            (reverse(
                'posts:profile',
                kwargs={'username': 'HasNoName'},
            ), 'posts/profile.html'),
            (reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk},
            ), 'posts/post_detail.html'),
            (reverse('posts:post_create'), 'posts/create_post.html'),
            (reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk},
            ), 'posts/create_post.html'),
        )
        for url, template in templates_url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

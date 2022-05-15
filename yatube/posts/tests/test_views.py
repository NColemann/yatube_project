import datetime
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings
from django.urls import reverse
from django import forms

from ..models import Group, Post, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user2 = User.objects.create_user(username='unknown')
        cls.user_other = User.objects.create_user(username='another')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа №2',
            slug='slug2',
            description='Описание группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.posts = [
            Post(
                pk=index,
                author=cls.user,
                text=f'Тестовый пост{index}',
                group=cls.group,
                image=uploaded,
            ) for index in range(1, 13)
        ]
        Post.objects.bulk_create(cls.posts, 12)
        for index, value in enumerate(cls.posts):
            minute = datetime.timedelta(minutes=index)
            value.pub_date += minute
        Post.objects.bulk_update(cls.posts, ['pub_date'])
        cls.post13 = Post.objects.create(
            author=cls.user_other,
            text='Тестовый пост13',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        cache.clear()

    def first_object_test(self, response):
        """Однотипные проверки первого объекта со страниц постов."""
        first_object = response.context.get('page_obj')[0]
        self.assertEqual(first_object, self.posts[11])
        self.assertEqual(first_object.image, self.posts[11].image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test-slug'},
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'HasNoName'},
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.posts[0].pk},
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.posts[0].pk},
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.first_object_test(response)

    def test_index_first_page_contains_ten_records(self):
        """Паджинатор на главной странице работает корректно."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_three_records(self):
        """Проверка: на второй странице / должно быть три поста."""
        response = self.authorized_client.get(
            reverse('posts:index'),
            {'page': 2},
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': 'test-slug'},
        ))
        self.first_object_test(response)
        self.assertEqual(response.context['group'], self.posts[11].group)

    def test_group_list_first_page_contains_ten_records(self):
        """Паджинатор на странице group/<slug>/ работает корректно."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug},
        ))
        response_group2 = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group2.slug},
        ))
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(len(response_group2.context['page_obj']), 0)

    def test_group_list_second_page_contains_two_records(self):
        """Проверка: на второй странице группы должно быть два поста."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug},
        ), {'page': 2})
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': 'HasNoName'},
        ))
        self.first_object_test(response)
        self.assertEqual(response.context['author'], self.user)
        self.assertEqual(response.context['count_obj'], len(self.posts))

    def test_profile_first_page_contains_ten_records(self):
        """Паджинатор на странице profile работает корректно."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': 'HasNoName'},
        ))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page_contains_two_records(self):
        """Проверка: на второй странице profile должно быть три поста."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': 'HasNoName'},
        ), {'page': 2})
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.posts[0].pk},
        ))
        self.assertEqual(response.context.get('post').text, 'Тестовый пост1')
        self.assertEqual(
            response.context.get('post').group.title,
            'Тестовая группа',
        )
        self.assertEqual(
            response.context.get('post').image,
            self.posts[0].image,
        )

    def test_post_form_show_correct_context(self):
        """Шаблон поста сформирован с правильным контекстом."""
        response_edit = self.authorized_client.get(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.posts[0].pk}
        ))
        response_create = self.authorized_client.get(reverse(
            'posts:post_create'
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field_edit = (
                    response_edit.context.get('form').fields.get(value)
                )
                self.assertIsInstance(form_field_edit, expected)
                form_field_create = (
                    response_create.context.get('form').fields.get(value)
                )
                self.assertIsInstance(form_field_create, expected)

    def test_cache_index_page(self):
        """Тестирование кеширования."""
        response = self.authorized_client.get(reverse('posts:index'))
        cache_check = response.content
        Post.objects.first().delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, cache_check)

    def test_without_cache_index_page(self):
        """Тестирование без кеша."""
        response = self.authorized_client.get(reverse('posts:index'))
        cache_check = response.content
        Post.objects.first().delete()
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, cache_check)

    def test_profile_follow(self):
        """Авторизованный пользователь может подписаться на автора."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_other.username},
        ))
        self.assertTrue(Follow.objects.filter(
            user=self.user,
            author=self.user_other,
        ).exists())

    def test_post_in_user_follower(self):
        """Пост автора есть в ленте подписанного пользователя."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_other.username},
        ))
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(self.post13, response.context['page_obj'])

    def test_post_not_in_user_not_follower(self):
        """Поста автора нет в ленте не подписанного пользователя."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user_other.username},
        ))
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post13, response.context['page_obj'])

    def test_profile_unfollow(self):
        """Авторизованный пользователь может отписаться от автора."""
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user_other.username},
        ))
        self.assertFalse(Follow.objects.filter(
            user=self.user,
            author=self.user_other,
        ).exists())

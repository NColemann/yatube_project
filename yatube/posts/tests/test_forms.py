import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.urls import reverse

from ..models import Group, Post
from ..forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
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
            content_type='image/gif',
        )
        form_data = {
            'text': 'Тест формы',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        new_post = Post.objects.first()
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'HasNoName'},)
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group.pk, self.group.pk)
        self.assertEqual(new_post.image, 'posts/small.gif')

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тест формы редактирования',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        edit_post = Post.objects.get(pk=self.post.pk)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.author, self.user)
        self.assertEqual(edit_post.group.pk, self.group.pk)

    def test_add_comment(self):
        """Авторизованный пользователь может комментировать посты."""
        form_data = {
            'text': 'Комментарий',
        }
        response = self.authorized_client.post(reverse(
            'posts:add_comment',
            kwargs={'post_id': self.post.pk},
        ), data=form_data, follow=True)
        response_post = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk},
        ))
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk},
        ))
        self.assertEqual(
            response_post.context['comments'][0].text,
            form_data['text'],
        )
        self.assertEqual(response_post.context['post'], self.post)
        self.assertEqual(
            response_post.context['comments'][0].author,
            self.user,
        )

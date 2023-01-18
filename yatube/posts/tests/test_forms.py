import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст',
            'image': self.uploaded,
        }
        create_response = self.authorized_client.post(
            reverse('posts:post_create'),
            form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.last()
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.image, 'posts/small.gif')
        self.assertEqual(post.group, self.group)
        self.assertEqual(self.group.posts.count(), 1)
        self.assertEqual(create_response.status_code, HTTPStatus.OK)

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        post = Post.objects.create(
            text='Текст поста',
            author=self.user,
            group=self.group,
            image=self.uploaded,
        )
        new_group = Group.objects.create(
            title='Тестовая группа',
            slug='test-new-slug',
            description='Тестовое описание',
        )
        new_form_data = {
            'text': 'новый текст',
            'group': new_group.id,
            'image': self.uploaded,
        }
        edit_response = self.authorized_client.post(
            reverse('posts:post_edit', args=(post.id,)),
            new_form_data,
            follow=True
        )
        post.refresh_from_db()
        self.assertEqual(edit_response.status_code, HTTPStatus.OK)
        self.assertEqual(post.author, self.user)
        self.assertNotEqual(post.text, new_form_data['text'])
        self.assertNotEqual(post.group.id, new_group.id)
        self.assertEqual(self.group.posts.count(), 1)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testAuthorized')
        cls.author = User.objects.create_user(username='testAuthor')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Длинный тестовый пост',
            group=cls.group
        )

        cls.post_detail_url = reverse(
            'posts:post_detail', args=(cls.post.id,)
        )
        cls.comment_url = reverse(
            'posts:add_comment', args=(cls.post.id,)
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_comments_post(self):
        """Авторизованный пользователь может комментировать записи"""
        text = 'Длинный комментарий'
        comment_response = self.authorized_client.post(
            self.comment_url,
            {'text': text},
            follow=True
        )
        comment = Comment.objects.latest('created')
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.text, text)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertRedirects(
            comment_response, self.post_detail_url
        )

    def test_guest_client_not_allowed_comment_post(self):
        """Незарегистрированный пользователь не может комментировать записи"""
        comment_guest_redirect_url = (
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )
        text = 'Комментарий гостя'
        comment_response = self.guest_client.post(
            self.comment_url,
            {'text': text},
            follow=True
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(
            comment_response, comment_guest_redirect_url
        )

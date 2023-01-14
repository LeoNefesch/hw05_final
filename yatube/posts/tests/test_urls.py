from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Текст поста',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.index_url = '/'
        self.group_list_url = '/group/test-slug/'
        self.profile_url = f'/profile/{self.user.username}/'
        self.post_detail_url = f'/posts/{self.post.id}/'
        self.post_create_url = '/create/'
        self.post_edit_url = f'/posts/{self.post.id}/edit/'
        cache.clear()

    def test_urls_correct_ctatus_code(self):
        """Соответсвие URL-адреса страницы и статуса ответа
        для неавторизованного пользователя."""
        url_names = {
            self.index_url: HTTPStatus.OK,
            self.group_list_url: HTTPStatus.OK,
            self.profile_url: HTTPStatus.OK,
            self.post_detail_url: HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, status in url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_post_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(self.post_create_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница /posts/<post_id>/edit/ доступна авторизованному
        пользователю."""
        response = self.authorized_client.get(self.post_edit_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(self.post_create_url, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу /posts/{self.post.id}/edit/ перенаправит
        анонимного пользователя на страницу логина.
        """
        response = self.guest_client.get(
            self.post_edit_url, follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.index_url: 'posts/index.html',
            self.group_list_url: 'posts/group_list.html',
            self.profile_url: 'posts/profile.html',
            self.post_detail_url: 'posts/post_detail.html',
            self.post_create_url: 'posts/create_post.html',
            self.post_edit_url: 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

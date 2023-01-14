from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post
from posts.paginators import NUMBER_OF_POSTS

User = get_user_model()


class ViewsTests(TestCase):
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
        # cls.comment_post = Comment.objects.create(
        #     author=cls.user,
        #     text='Тестовый коммент',
        #     post=cls.post
        # )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            # '/': 'posts/index.html',
            (reverse('posts:group_list', args=('test-slug',))):
                'posts/group_list.html',
            '/group/test-slug/': 'posts/group_list.html',
            (reverse('posts:profile', args=(self.post.author,))):
                'posts/profile.html',
            (reverse('posts:post_detail', args=(self.post.id,))):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse('posts:post_edit', args=(self.post.id,))):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_uses_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        expected = list(Post.objects.all()[:NUMBER_OF_POSTS])
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', args=('test-slug',))
        )
        expected = list(
            Post.objects.filter(group_id=self.group.id)[:NUMBER_OF_POSTS]
        )
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', args=(self.post.author,))
        )
        expected = list(
            Post.objects.filter(author_id=self.user.id)[:NUMBER_OF_POSTS]
        )
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', args=(self.post.id,))
        )
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        self.assertIn('form', response.context)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=(self.post.id,))
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        self.assertIn('form', response.context)
        self.assertIn('is_edit', response.context)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Пост создан на страницах с выбранной группой"""
        form_fields = {
            reverse('posts:index'): Post.objects.get(group=self.post.group),
            reverse(
                'posts:group_list', args=('test-slug',)
            ): Post.objects.get(group=self.post.group),
            reverse(
                'posts:profile', args=('author',)
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context.get('page_obj')
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Созданный пост с группой не попал в чужую группу."""
        form_fields = {
            reverse(
                'posts:group_list', args=('test-slug',)
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context.get('page_obj')
                self.assertNotIn(expected, form_field)

    def test_comment_correct_context(self):
        """Валидная форма Комментария создает запись в Post."""
        # comments_count = Comment.objects.count()
        form_data = {"text": "Тестовый коммент"}
        response = self.authorized_client.post(
            reverse("posts:add_comment", args=(self.post.id, )),
            form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse(
                "posts:post_detail", args=(self.post.id, )
            )
        )
        self.assertEqual(Comment.objects.count(), 1)

    def test_check_cache(self):
        """Проверка кеша."""
        response = self.guest_client.get(reverse("posts:index"))
        r_1 = response.content
        Post.objects.get(id=1).delete()
        response2 = self.guest_client.get(reverse("posts:index"))
        r_2 = response2.content
        self.assertEqual(r_1, r_2)

    def test_follow_page(self):
        """Проверка подписки/отписки и страницу избранных постов """
        # Проверяем, что страница подписок пуста
        response = self.authorized_client.get(reverse("posts:follow_index"))
        # self.assertEqual(len(response.context["posts"]), 0)
        self.assertEqual(len(response.context['page_obj']), 0)

        # Проверка подписки на автора поста
        new_author = User.objects.create(username="ЛНТ")
        self.authorized_client.post(
            reverse("posts:profile_follow", args=(new_author,))
        )
        self.assertIs(
            Follow.objects.filter(user=self.user, author=new_author).exists(),
            True
        )

        # Проверка что пост не появился в избранных у юзера-обычного
        outsider = User.objects.create(username="NoName")
        self.authorized_client.force_login(outsider)
        self.assertIs(
            Follow.objects.filter(user=outsider, author=new_author).exists(),
            False
        )
        # Проверка отписки от автора поста
        self.authorized_client.force_login(self.user)
        self.authorized_client.post(
            reverse("posts:profile_unfollow", args=(new_author,))
        )
        self.assertIs(
            Follow.objects.filter(user=self.user, author=new_author).exists(),
            False
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        Post.objects.bulk_create(
            Post(
                text=f'Текст поста {i}',
                author=self.user,
                group=self.group,
            ) for i in range(13)
        )
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

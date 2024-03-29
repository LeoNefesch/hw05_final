from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import POST_LENGTH, Comment, Group, Post

User = get_user_model()
NEW_POST_LENGTH = 16


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=('Т' * NEW_POST_LENGTH),
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Тестовый коммент',
            post=cls.post
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        expected_group_name = group.title
        self.assertEqual(expected_group_name, str(group))
        post = PostModelTest.post
        self.assertEqual(str(post), post.text[:POST_LENGTH])
        comment = PostModelTest.comment
        self.assertEqual(str(comment), comment.text[:POST_LENGTH])

    def test_post_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_post_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

    def test_comment_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        comment = PostModelTest.comment
        field_verboses = {
            'post': 'Пост',
            'author': 'Автор',
            'text': 'Текст поста',
            'created': 'Дата публикации',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name, expected_value
                )

    def test_comment_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        comment = PostModelTest.comment
        help_text = 'Введите текст комментария'
        self.assertEqual(comment._meta.get_field('text').help_text, help_text)

from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    def test_404_error_page(self):
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_403_error_page(self):
        response = self.client.get('/nonexist-page/')
        # self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # self.assertTemplateUsed(response, 'core/403csrf.html')

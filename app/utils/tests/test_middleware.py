from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from utils.middleware import ApiNoStoreMiddleware


def _call(path):
    middleware = ApiNoStoreMiddleware(lambda request: HttpResponse("ok"))
    return middleware(RequestFactory().get(path))


class ApiNoStoreMiddlewareTest(SimpleTestCase):
    def test_registered_in_settings(self):
        self.assertIn("utils.middleware.ApiNoStoreMiddleware", settings.MIDDLEWARE)

    def test_api_response_is_not_cached(self):
        cache_control = _call("/api/v1/some-endpoint/").headers["Cache-Control"]
        self.assertIn("no-store", cache_control)
        self.assertIn("private", cache_control)

    def test_non_api_response_is_untouched(self):
        self.assertNotIn("Cache-Control", _call("/startup/").headers)

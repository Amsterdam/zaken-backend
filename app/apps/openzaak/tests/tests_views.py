from django.urls import reverse

from django_webtest import WebTest

from apps.openzaak.models import Notification


class ViewTests(WebTest):
    def test_notification_get(self):
        url = reverse("notification-callback")
        self.app.get(url, status=405)

    def test_notification_post(self):
        url = reverse("notification-callback")
        response = self.app.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.data, "{}")

    def test_notification_post_with_data(self):
        url = reverse("notification-callback")
        response = self.app.post(url, params={"test": "test"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.data, '{"test": "test"}')

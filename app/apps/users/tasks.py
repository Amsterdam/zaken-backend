from celery import shared_task
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone

"""
Celery task that deactivates users who have not logged in within the past 6 months
(including users who have never logged in). Staff users and users holding an active
auth token (regular or scoped) are exempt, since those tokens indicate ongoing
programmatic or delegated access.

Deactivated users cannot log in until an admin reactivates their account.
"""


@shared_task
def deactivate_inactive_users():
    User = get_user_model()
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    inactive_users = User.objects.filter(
        Q(last_login__lt=six_months_ago) | Q(last_login__isnull=True),
        is_active=True,
        is_staff=False,
    ).filter(auth_token__isnull=True, scoped_auth_tokens__isnull=True)
    for user in inactive_users:
        user.is_active = False
        user.save()

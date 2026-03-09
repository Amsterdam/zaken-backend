from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

"""
Celery task to deactivate users who have not logged in for more than 6 months.
"""


@shared_task
def deactivate_inactive_users():
    User = get_user_model()
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    inactive_users = User.objects.filter(
        is_active=True, last_login__lt=six_months_ago, is_staff=False
    )
    for user in inactive_users:
        user.is_active = False
        user.save()

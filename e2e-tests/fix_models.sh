#!/bin/bash
docker-compose -f docker-compose.local.yml run --rm zaak-gateway python manage.py shell -c "
from django.contrib.auth import get_user_model
get_user_model().objects.get_or_create(email='local.user@dev.com', first_name='local', last_name='user')"

docker-compose -f docker-compose.local.yml run --rm zaak-gateway python manage.py shell -c "
from apps.users.models import User, UserGroup
from django.contrib.auth.models import Permission
(group, _) = UserGroup.objects.get_or_create(name='PROJECTHANDHAVER', display_name='Projecthandhaver')
group.permissions.add(Permission.objects.get(name='Close a Case (by performing the last task)'))
group.permissions.add(Permission.objects.get(name='Create a new Case'))
group.permissions.add(Permission.objects.get(name='Can perform a tasks'))
group.permissions.add(Permission.objects.get(name='Can read gevoelige dossiers'))
user = User.objects.get(email='local.user@dev.com')
user.groups.add(group)"

docker-compose -f docker-compose.local.yml run --rm zaak-gateway python manage.py shell -c "
from django_celery_beat.models import PeriodicTask, IntervalSchedule
schedule, created = IntervalSchedule.objects.get_or_create(every=10, period=IntervalSchedule.SECONDS)
PeriodicTask.objects.get_or_create(interval=schedule, name='Update workflows', task='apps.workflow.tasks.task_update_workflows')"

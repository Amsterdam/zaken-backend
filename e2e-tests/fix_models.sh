#!/bin/bash
docker-compose run --rm zaak-gateway python manage.py shell -c "
from apps.users.models import User, UserGroup
from django.contrib.auth.models import Permission
(group, _) = UserGroup.objects.get_or_create(name='PROJECTHANDHAVER', display_name='Projecthandhaver')
group.permissions.add(Permission.objects.get(name='Close a Case (by performing the last task)'))
group.permissions.add(Permission.objects.get(name='Create a new Case'))
group.permissions.add(Permission.objects.get(name='Can perform a tasks'))
user = User.objects.get(email='local.user@dev.com')
user.groups.add(group)"

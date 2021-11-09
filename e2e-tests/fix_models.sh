#!/bin/bash

docker-compose run --rm zaak-gateway python manage.py shell -c "from apps.summons.models import SummonType; SummonType.objects.get_or_create(workflow_option='sluiting', name='Sluiting', theme_id=1); SummonType.objects.get_or_create(workflow_option='legalisatie-brief', name='Legalisatie-brief', theme_id=1);"

docker-compose run --rm zaak-gateway python manage.py shell -c "from apps.summons.models import SummonType;
for id in [1,2,3]:
    summon_type = SummonType.objects.get(pk=id);
    summon_type.workflow_option = 'waarschuwingsbrief';
    summon_type.save()"

docker-compose run --rm zaak-gateway python manage.py shell -c "from apps.decisions.models import DecisionType; DecisionType.objects.get_or_create(workflow_option='no_decision', name='Afzien voornemen', is_sanction=False, theme_id=1)"

docker-compose run --rm zaak-gateway python manage.py shell -c "
from django.contrib.auth import get_user_model
get_user_model().objects.get_or_create(email='local.user@dev.com', first_name='local', last_name='user')"

docker-compose run --rm zaak-gateway python manage.py shell -c "
from django_celery_beat.models import PeriodicTask, IntervalSchedule
schedule, created = IntervalSchedule.objects.get_or_create(every=10, period=IntervalSchedule.SECONDS)
PeriodicTask.objects.get_or_create(interval=schedule, name='Update workflows', task='apps.workflow.tasks.task_update_workflows')"

docker-compose run --rm zaak-gateway python manage.py shell -c "
from apps.workflow.models import WorkflowOption
taks, created = WorkflowOption.objects.get_or_create(name='Aanschrijving toevoegen', message_name='aanschrijving_toevoegen', to_directing_proccess=True, theme_id=1)"

docker-compose run --rm zaak-gateway python manage.py shell -c "
from apps.users.models import User, UserGroup
from django.contrib.auth.models import Permission
(group, _) = UserGroup.objects.get_or_create(name='PROJECTHANDHAVER', display_name='Projecthandhaver')
group.permissions.add(Permission.objects.get(name='Close a Case (by performing the last task)'))
group.permissions.add(Permission.objects.get(name='Create a new Case'))
group.permissions.add(Permission.objects.get(name='Can perform a tasks'))
user = User.objects.get(email='local.user@dev.com')
user.groups.add(group)"

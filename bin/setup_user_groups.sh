#!/bin/bash

WEB_SERVICE_NAME="zaak-gateway"

docker compose -f docker-compose.local.yml run -T --rm "${WEB_SERVICE_NAME}" python manage.py shell <<PY

from apps.users.models import User, UserGroup
from django.contrib.auth.models import Permission

(group, _) = UserGroup.objects.get_or_create(name='BRP_GEGEVENS_INZIEN', display_name='BRP gegevens inzien')
group.permissions.add(Permission.objects.get(codename="access_personal_data_register"))

(group, _) = UserGroup.objects.get_or_create(name='PROJECTMEDEWERKER', display_name='Projectmedewerker')
group.permissions.add(Permission.objects.get(codename="access_business_register"))
group.permissions.add(Permission.objects.get(codename="access_recovery_check"))
group.permissions.add(Permission.objects.get(codename="close_case"))
group.permissions.add(Permission.objects.get(codename="create_case"))
group.permissions.add(Permission.objects.get(codename="perform_task"))

(group, _) = UserGroup.objects.get_or_create(name='TOEZICHTHOUDER', display_name='Toezichthouder')
group.permissions.add(Permission.objects.get(codename="perform_task"))

(group, _) = UserGroup.objects.get_or_create(name='PROJECTHANDHAVER', display_name='Projecthandhaver')
group.permissions.add(Permission.objects.get(codename="access_business_register"))
group.permissions.add(Permission.objects.get(codename="access_recovery_check"))
group.permissions.add(Permission.objects.get(codename="perform_task"))

(group, _) = UserGroup.objects.get_or_create(name='HANDHAVINGSJURIST', display_name='Handhavingsjurist')
group.permissions.add(Permission.objects.get(codename="access_business_register"))
group.permissions.add(Permission.objects.get(codename="access_recovery_check"))
group.permissions.add(Permission.objects.get(codename="perform_task"))

(group, _) = UserGroup.objects.get_or_create(name='MEDEWERKER_GEVOELIGE_ZAKEN', display_name='Medewerker Gevoelige Zaken')
group.permissions.add(Permission.objects.get(codename="access_sensitive_dossiers"))

(group, _) = UserGroup.objects.get_or_create(name='PROJECTMEDEWERKER_DIGITAAL_TOEZICHT', display_name='Projectmedewerker - Digitaal Toezicht')
group.permissions.add(Permission.objects.get(codename="create_digital_surveilance_case"))

(group, _) = UserGroup.objects.get_or_create(name='TOEZICHTHOUDER_DIGITAAL_TOEZICHT', display_name='Toezichthouder - Digitaal toezicht')
group.permissions.add(Permission.objects.get(codename="access_sigital_surveillance"))
group.permissions.add(Permission.objects.get(codename="create_digital_surveilance_case"))

PY

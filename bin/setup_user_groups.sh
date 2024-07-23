echo  "from apps.users.models import User, UserGroup
from django.contrib.auth.models import Permission

(group, _) = UserGroup.objects.get_or_create(name='PROJECTMEDEWERKER', display_name='Projectmedewerker')
group.permissions.add(Permission.objects.get(name=\"Can access 'Handelsregister' (bedrijfseigenaren van panden, bedrijfsinformatie)\"))
group.permissions.add(Permission.objects.get(name=\"Can access 'BRP' (persoonsgegevens / ingeschreven personen)\"))
group.permissions.add(Permission.objects.get(name=\"Can access 'invorderingscheck'\"))
group.permissions.add(Permission.objects.get(name='Close a Case (by performing the last task)'))
group.permissions.add(Permission.objects.get(name='Create a new Case'))
group.permissions.add(Permission.objects.get(name='Can perform a tasks'))

(group, _) = UserGroup.objects.get_or_create(name='TOEZICHTHOUDER', display_name='Toezichthouder')
group.permissions.add(Permission.objects.get(name=\"Can access 'BRP' (persoonsgegevens / ingeschreven personen)\"))
group.permissions.add(Permission.objects.get(name='Can perform a tasks'))

(group, _) = UserGroup.objects.get_or_create(name='PROJECTHANDHAVER', display_name='Projecthandhaver')
group.permissions.add(Permission.objects.get(name=\"Can access 'Handelsregister' (bedrijfseigenaren van panden, bedrijfsinformatie)\"))
group.permissions.add(Permission.objects.get(name=\"Can access 'BRP' (persoonsgegevens / ingeschreven personen)\"))
group.permissions.add(Permission.objects.get(name=\"Can access 'invorderingscheck'\"))
group.permissions.add(Permission.objects.get(name='Can perform a tasks'))

(group, _) = UserGroup.objects.get_or_create(name='HANDHAVINGSJURIST', display_name='Handhavingsjurist')
group.permissions.add(Permission.objects.get(name=\"Can access 'Handelsregister' (bedrijfseigenaren van panden, bedrijfsinformatie)\"))
group.permissions.add(Permission.objects.get(name=\"Can access 'BRP' (persoonsgegevens / ingeschreven personen)\"))
group.permissions.add(Permission.objects.get(name=\"Can access 'invorderingscheck'\"))
group.permissions.add(Permission.objects.get(name='Can perform a tasks'))

(group, _) = UserGroup.objects.get_or_create(name='MEDEWERKER GEVOELIGE ZAKEN', display_name='Medewerker Gevoelige Zaken')
group.permissions.add(Permission.objects.get(name='Can read gevoelige dossiers'))

(group, _) = UserGroup.objects.get_or_create(name='PROJECTMEDEWERKER_DIGITAAL_TOEZICHT', display_name='Projectmedewerker - Digitaal Toezicht')
group.permissions.add(Permission.objects.get(name=\"Create a new 'Digitaal toezicht' Case\"))

(group, _) = UserGroup.objects.get_or_create(name='TOEZICHTHOUDER_DIGITAAL_TOEZICHT', display_name='Toezichthouder - Digitaal toezicht')
group.permissions.add(Permission.objects.get(name=\"Can read 'Digitaal toezicht'\"))
group.permissions.add(Permission.objects.get(name=\"Create a new 'Digitaal toezicht' Case\"))" | docker-compose -f docker-compose.local.yml run -T --rm zaak-gateway python manage.py shell


# # Creates a superuser for the zaak-gateway backend
echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin@admin.com', 'admin')" | docker-compose run --rm zaak-gateway python manage.py shell

# # Creates a superuser for the openzaak backend
echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')" | docker-compose run --rm openzaak.local python src/manage.py shell
echo "from vng_api_common.models import JWTSecret; from vng_api_common.authorizations.models import Applicatie, Autorisatie; secret = JWTSecret.objects.create(identifier='Zaken', secret='Zaken'); app = Applicatie.objects.create(label='Zaken', client_ids=[secret], heeft_alle_autorisaties=True); Autorisatie.objects.create(applicatie=app, scopes=[])" |  docker-compose run --rm openzaak.local python src/manage.py shell


# # Creates a superuser for the zaak-gateway backend
echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin@admin.com', 'admin')" | docker-compose run --rm zaak-gateway python manage.py shell

# # Creates a superuser for the openzaak backend
echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin')" | docker-compose run --rm openzaak.local python src/manage.py shell
echo "from vng_api_common.models import JWTSecret; from vng_api_common.authorizations.models import Applicatie, Autorisatie; from vng_api_common.constants import ComponentTypes; from openzaak.components.autorisaties.api.scopes import SCOPE_AUTORISATIES_LEZEN, SCOPE_AUTORISATIES_BIJWERKEN; secret = JWTSecret.objects.create(identifier='Zaken', secret='Zaken'); app = Applicatie.objects.create(label='Zaken',client_ids=[secret]); Autorisatie.objects.create(applicatie=app,component=ComponentTypes.ac, scopes=[SCOPE_AUTORISATIES_LEZEN, SCOPE_AUTORISATIES_BIJWERKEN])" |  docker-compose run --rm openzaak.local python src/manage.py shell

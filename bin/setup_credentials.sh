# Creates a superuser for the zaak-gateway backend
echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin@admin.com', 'admin')" | docker-compose -f docker-compose.local.yml run --rm zaak-gateway python manage.py shell

# Creates a superuser for the zaak-gateway backend
echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin@admin.com', 'insecure')" | docker-compose -f docker-compose.local.yml run -T --rm zaak-gateway python manage.py shell

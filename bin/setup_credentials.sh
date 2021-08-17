# Creates a superuser for the zaak-gateway backend
echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin@admin.com', 'admin')" | docker-compose run --rm zaak-gateway python manage.py shell

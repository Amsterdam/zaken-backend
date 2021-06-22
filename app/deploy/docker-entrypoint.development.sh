# Same as entrypoint.sh, but with py-auto-reload enabled to allow auto reloading when making changes during development
#!/usr/bin/env bash
set -u   # crash on missing env variables
set -e   # stop on any error
set -x

until PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOST -U $DATABASE_USER -c '\q'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "Postgres is up!"

echo Collecting static files
python manage.py collectstatic --no-input
chmod -R 777 /static

# echo Clear tables
# python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('drop table if exists "django_migrations" cascade; drop table if exists "django_content_type" cascade; drop table if exists "auth_permission" cascade; drop table if exists "auth_group" cascade; drop table if exists "auth_group_permissions" cascade; drop table if exists "users_user" cascade; drop table if exists "users_user_groups" cascade; drop table if exists "users_user_user_permissions" cascade; drop table if exists "django_admin_log" cascade; drop table if exists "django_session" cascade;'); cursor.close();"

echo Apply migrations
python manage.py migrate --noinput

echo Axes check
python manage.py check

# echo Create root user
# python manage.py shell -c "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin@admin.com', 'admin')"

# opens up a port for attaching a remote debugging service using debugpy
python -m debugpy --listen 0.0.0.0:5678 ./manage.py runserver 0.0.0.0:8000

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

echo Apply migrations
python manage.py migrate --noinput

echo Create root user
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('ALTER TABLE django_admin_log ALTER COLUMN user_id TYPE uuid'); cursor.close();"
python manage.py shell -c "from apps.users.models import User; User.objects.all().delete()"
python manage.py shell -c "from apps.users.models import User; User.objects.create_superuser('admin@admin.com', 'admin')"

exec uwsgi --ini /app/deploy/config.ini --py-auto-reload=1

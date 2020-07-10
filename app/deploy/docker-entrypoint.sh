#!/usr/bin/env bash
set -u   # crash on missing env variables
set -e   # stop on any error
set -x

until PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOST -U $DATABASE_USER -c '\q'; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done
echo "Postgres is up!"

python manage.py reset_db --noinput

echo Collecting static files
python manage.py collectstatic --no-input
chmod -R 777 /static

echo Apply migrations
python manage.py migrate --noinput


echo Create root user
python manage.py shell -c "from apps.users.models import User; User.objects.create_superuser('admin@admin.com', 'admin')"

exec uwsgi --ini /app/deploy/config.ini --py-auto-reload=1

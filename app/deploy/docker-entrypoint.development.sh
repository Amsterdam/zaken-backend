#!/usr/bin/env bash
set -u   # crash on missing env variables
set -e   # stop on any error
set -x

until PGPASSWORD=$DATABASE_PASSWORD psql -h $DATABASE_HOST -U $DATABASE_USER -c '\q'; do
  echo "Postgres is unavailable - sleeping"
  sleep 5
done
echo "Postgres is up!"



echo Collecting static files
python manage.py collectstatic --no-input

echo Apply migrations
python manage.py migrate --noinput

echo Axes check
python manage.py check
python manage.py axes_reset

python manage.py loaddata fixture

exec python -m debugpy --listen 0.0.0.0:5678 ./manage.py runserver 0.0.0.0:8000

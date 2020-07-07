#!/usr/bin/env bash
set -u   # crash on missing env variables
set -e   # stop on any error
set -x

echo Collecting static files
python manage.py collectstatic --no-input
chmod -R 777 /static

echo Apply migrations
python manage.py migrate --noinput

exec uwsgi --ini /app/deploy/config.ini --py-auto-reload=1

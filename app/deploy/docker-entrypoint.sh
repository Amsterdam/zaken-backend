#!/usr/bin/env bash
set -u   # crash on missing env variables
set -e   # stop on any error
set -x

echo Collecting static files
python manage.py collectstatic --no-input

echo Apply migrations
python manage.py migrate --noinput

echo Axes check
python manage.py check
python manage.py axes_reset

python manage.py loaddata fixture

exec "$@"

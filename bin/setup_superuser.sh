#!/bin/bash

# Creates a superuser for the given `email` address, or updates if it already exists.
#
# Example usage:
# ./bin/setup_superuser.sh user@amsterdam.nl

if [ -z "$1" ]; then
    echo "Usage: $0 <email>"
    exit 1
fi

WEB_SERVICE_NAME="zaak-gateway"
EMAIL="$1"

docker compose -f docker-compose.local.yml run -T --rm "${WEB_SERVICE_NAME}" python manage.py shell <<PY
from django.contrib.auth import get_user_model

User = get_user_model()
email = "${EMAIL}"

user, created = User.objects.get_or_create(email=email, username=email)

user.is_staff = True
user.is_superuser = True
user.is_active = True

user.save()

print(f"{'Created' if created else 'Updated'} superuser for {email}")
PY

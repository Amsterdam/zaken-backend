#!/bin/bash

# Creates a superuser for in AZA
echo "from django.contrib.auth import get_user_model; get_user_model().objects.create_superuser('admin@admin.com', 'admin')" | python local.py shell >/dev/null 2>&1

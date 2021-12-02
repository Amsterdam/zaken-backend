#!/bin/bash

docker-compose down

docker volume rm $(docker volume ls -q)

docker-compose -f ../docker-compose.test.yml build

docker-compose run --rm zaak-gateway python manage.py migrate

bash ../bin/setup_credentials.sh

./fix_models.sh

docker-compose -f ../docker-compose.test.yml up

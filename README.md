# Zaken
Zakensysteem bedoeld voor toezichthouders en handhavers van illegaal vakantieverhuur.

## Prerequisites
Make sure you have Docker installed locally:
- [Docker](https://docs.docker.com/docker-for-mac/install/)

## Getting up and running
Once you have Docker installed, make sure it's running.
To build and start the project, run:
```bash
docker-compose up --build
```

If you are running this application without having run the fixxx-looplijsten-backend first, make sure a network is created first:
```
docker network create fixxx-looplijsten-backend_looplijsten_backend
```

## Django backend
The Django backend application can be accessed through port 8080:
```
localhost:8080
```

You can run manage commands as follows:
```
docker-compose run --rm zaak-gateway python manage.py makemigrations
```

You can create a superuser account as follows:
```
docker-compose run --rm zaak-gateway python manage.py createsuperuser
```
Follow the steps, and you'll be able to sign into http://localhost:8080/admin/

## Accessing the API documentation
You can access the documentation at:
http://localhost:8080/api/v1/swagger/

## Generating an access token
When the LOCAL_DEVELOPMENT_AUTHENTICATION environment variable is set to True, you can gain access easily in the Swagger documentation by executing the /api/v1/oidc-authenticate/ POST request.
You can use the 'access' token in the response:
Click on the 'Authorize' button in the top right corner of the page, and enter the given access token.
This allows you to execute the API endpoints in the page.

## Generating Mock Data
You can generate mock data easily (from the API swagger environment) by executing the /api/v1/generate-mock/ GET request.

## Adding pre-commit hooks
You can add pre-commit hooks for checking and cleaning up your changes:
```
bash install.sh
```

You can also run the following command to ensure all files adhere to coding conventions:
```
bash cleanup.sh
```
This will autoformat your code, sort your imports and fix overal problems.

## Coding conventions and style
The project uses [Black](https://github.com/psf/black) for formatting and [Flake8](https://pypi.org/project/flake8/) for linting.

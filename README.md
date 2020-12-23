# Zaken
Zakensysteem bedoeld voor toezichthouders en handhavers van illegaal vakantieverhuur.

## Prerequisites
Make sure you have Docker installed locally:
- [Docker](https://docs.docker.com/docker-for-mac/install/)

## Getting up and running
Once you have Docker installed, make sure it's running.
First create the external networks using the following commands:
```bash
docker network create zaken_network
```
```bash
docker network create top_and_zaak_backend_bridge
```

Next, build the project:
```bash
docker-compose build
```

To start the project, run:
```bash
docker-compose up
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
bash bin/install_pre_commit.sh
```

You can also run the following command to ensure all files adhere to coding conventions:
```
bash bin/cleanup_pre_commit.sh
```
This will autoformat your code, sort your imports and fix overal problems.

## Coding conventions and style
The project uses [Black](https://github.com/psf/black) for formatting and [Flake8](https://pypi.org/project/flake8/) for linting.

## Health check
A path is available for checking the health of the running application, and all its connected services.
The overview of this status can be found on the following path: {application_url}/health
To improve reliability, the health checks should be expanded for each essential service that is added to the application. For more on how to expand the health checks, read the [Django Healh Check documentation](https://github.com/KristianOellegaard/django-health-check).

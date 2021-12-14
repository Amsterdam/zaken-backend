# Zaken

Zakensysteem bedoeld voor toezichthouders en handhavers van illegaal vakantieverhuur.

## Prerequisites

Make sure you have Docker installed locally:

- [Docker](https://docs.docker.com/docker-for-mac/install/)

## Getting up and running (Local development only)

These steps are necessary to make sure all configurations are set up correctly so that you can get the project running correctly.

First, make sure you have built the project and executed the database migrations:

```
docker network create top_and_zaak_backend_bridge
docker network create zaken_network
docker-compose build
docker-compose run --rm zaak-gateway python manage.py migrate
```

To create all necessary credentials run the following command:

```
bash bin/setup_credentials.sh
```

This will create superuser admin account with the following credentials

```
email: admin@admin.com
password: admin
```

Start AZA backend:

```
docker-compose up
```

Visit the Admin at http://localhost:8080/admin/

Check the health page to see if all services are up and running:
http://localhost:8080/health

## Running tests

Run unit tests locally with:

```
docker-compose run --rm zaak-gateway python manage.py test
```

To run tests for a specific module, add a path:

```
docker-compose run --rm zaak-gateway python manage.py test ./apps/cases/tests
```

## Accessing the API documentation

You can access the documentation at:
http://localhost:8080/api/v1/swagger/

## Generating an access token

When the LOCAL_DEVELOPMENT_AUTHENTICATION environment variable is set to True, you can gain access easily in the Swagger documentation by executing the /api/v1/oidc-authenticate/ POST request.
You can use the 'access' token in the response:
Click on the 'Authorize' button in the top right corner of the page, and enter the given access token.
This allows you to execute the API endpoints in the page.

## Enabling Keycloak authentication for a locally run zaken-frontend

Set LOCAL_DEVELOPMENT_AUTHENTICATION environment variable to False

## Generating Mock Data

You can generate mock data easily (from the API swagger environment) by executing the /api/v1/generate-mock/ GET request.

## Update fixtures

Generate new fixtures json file:

```
docker-compose run --rm zaak-gateway python manage.py dumpdata --indent 2 -o temp_fixture.json [app_name]
```

Now manually copy changes you need to the corresponding fixtures file.

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

## Generating Model Graph

It's possible to generate a graph of the datamodel using the following command:

```
docker-compose run --rm zaak-gateway python manage.py graph_models cases debriefings permits fines addresses events visits summons -X ModelEventEmitter,ModelEditableTimeConstraint,ModelEditablelBase --pygraphviz -o diagram.png
```

Note that the apps and models should be updated whenever applications and models are added or modified.

# FAQ

_Error: Account locked: too many login attempts. Contact an admin to unlock your account._

Cause: somebody tried to login with too many failed attempts. Unfortunately we have not
configured Axes properly so if one user does this, every user is locked.

Resolution: SSH into the webserver and run `python manage.py axes_reset`

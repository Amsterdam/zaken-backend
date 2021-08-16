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

This will create superuser admin accounts with the following credentials:

For Zaken Admin, located at http://localhost:8080/admin/

```
email: admin@admin.com
password: admin
```

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
docker-compose run --rm zaak-gateway python manage.py graph_models cases camunda debriefings permits fines addresses events visits summons -X ModelEventEmitter,ModelEditableTimeConstraint,ModelEditablelBase --pygraphviz -o diagram.png
```

Note that the apps and models should be updated whenever applications and models are added or modified.

## Camunda

Camunda Cockpit: `http://localhost:7000/camunda`
Camunda REST engine: `http://localhost:7000/engine-rest`.
[Documentation](https://docs.camunda.org/manual/latest/reference/rest/)

## Camunda process deploying

The easiest way to do this is to download the [Camunda Modeler](https://camunda.com/download/modeler/) and use its "Deploy current diagram" function (It is in the toolbar topside al the way to the right next to the play button (start process instance) button. It looks like a horizontal bar with an up arrow on top of it). Makeup a good deployment name and for the REST Endpoint type the url of the base api endpoint. For localhost it is `http://localhost:7000/engine-rest` (NOTE: no end slash) otherwise consult app settings for different environments.

You can also deploy via the REST endpoint with the following settings.

```
URL: http://localhost:7000/engine-rest/deployment/create
Headers
Content-Type: multipart/form-data
Authorization: test1234

Body
upload: file.bpmn
deployment-name: zaak_wonen_vakantieverhuur (for example. see settings.py for camunda deployments)
```

Or you could use curl like below.

```
curl -v -F "deployment-name=process_name" -F "upload=@path-to-file.bpmn" "http://localhost:7000/engine-rest/deployment/create" -H "Authorization: test1234"
```

Or do them all at once:

```
for i in camunda/src/main/resources/bpmn/* ; do curl -v -F "deployment-name=`basename -s ".bpmn" $i`" -F "upload=@$i" "http://localhost:7000/engine-rest/deployment/create" -H "Authorization: test1234" ; done
```

(_Don't forget to change the version tag_ Camunda will make one for you if you don't but make it nice and correct ;). if you can find the context menu where you can change the version tag: switch to XML mode and search for the `camunda:versionTag` attribute and change it there.)

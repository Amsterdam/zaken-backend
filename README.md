# Zaken
Zakensysteem bedoeld voor toezichthouders en handhavers van illegaal vakantieverhuur.

## Prerequisites
Make sure you have Docker installed locally:
- [Docker](https://docs.docker.com/docker-for-mac/install/)

## Getting up and running (Local development only)
These steps are necessary to make sure all configurations are set up correctly so that you can get the project running, and Zaak Gateway and OpenZaak can communicate correctly.

First, make sure you have built the project and executed the database migrations:

```
docker network create top_and_zaak_backend_bridge
docker network create zaken_network
docker-compose build
docker-compose run --rm zaak-gateway python manage.py migrate
docker-compose run --rm openzaak.local python src/manage.py migrate
```

To create all necessary credentials run the following command:

```
bash bin/setup_credentials.sh
```

This will create superuser admin accounts with the following credentials:

For Zaken Admin, located at http://localhost:8080/admin/:
```
email: admin@admin.com
password: admin
```

For OpenZaak, located at http://localhost:8090/admin/
```
username: admin
password: admin
```

It will also register an application for authorising access to OpenZaak.
The credentials for this Zaken - OpenZaak connection are the defaults set in the .env environment variables:
```
OPEN_ZAAK_CLIENT=Zaken
OPEN_ZAAK_SECRET_KEY=Zaken
```
This application is not completely authorised yet, and one manual step is still necessary.
Make sure the containers are running:

```
docker-compose up
```

Once everything is running, sign into the OpenZaak admin (http://localhost:8080/admin/).
Select the Zaken application in the applications, which can be found under API Autorisaties -> Applicaties.
Here, make sure the 'Heeft alle autorisaties' checkbox is checked and press 'Opslaan' to save.

Now the Zaken application is fully authorised for adding and retrieving resources from the OpenZaak instance.
This is done using ZGW Consumers, which need to be configured in the Zaken backend. To do this automatically run:

```
docker-compose run --rm zaak-gateway python manage.py initialize_openzaak
```
This management command will create the consumers, and the basic data structures needed in OpenZaak.

Once this has finished running, you're done with the local configuration and setup.
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

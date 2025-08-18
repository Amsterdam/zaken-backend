# Amsterdamse Zaken Administratie (AZA)

Zakensysteem voor toezichthouders en handhavers van de Gemeente Amsterdam voor de thema's vakantieverhuur, kamerverhuur, ondermijning, leegstand, onderhuur en Opkoopbescherming.

- [Amsterdamse Zaken Administratie (AZA)](#amsterdamse-zaken-administratie-aza)
  - [Prerequisites](#prerequisites)
  - [Getting up and running (Local development only)](#getting-up-and-running-local-development-only)
  - [Running tests](#running-tests)
  - [API documentation (Swagger)](#api-documentation-swagger)
  - [Generating an access token](#generating-an-access-token)
  - [Enabling local development environment variables](#enabling-local-development-environment-variables)
  - [Enabling Keycloak authentication for a locally run zaken-frontend](#enabling-keycloak-authentication-for-a-locally-run-zaken-frontend)
  - [Generating Mock Data](#generating-mock-data)
  - [Update fixtures](#update-fixtures)
  - [Adding pre-commit hooks](#adding-pre-commit-hooks)
  - [Coding conventions and style](#coding-conventions-and-style)
  - [Health check](#health-check)
  - [Generating Model Graph](#generating-model-graph)
  - [Django DB migrations](#django-db-migrations)
- [FAQ](#faq)
- [BPMN-Modelling](#bpmn-modelling)
  - [Editing models](#editing-models)
  - [NOTE: Making changes](#note-making-changes)
  - [Deploy new BPMN-model with incremented version](#deploy-new-bpmn-model-with-incremented-version)
  - [Important learnings](#important-learnings)
    - [Forms](#forms)
    - [User tasks](#user-tasks)


## Prerequisites

Make sure you have Docker installed locally:

- [Docker](https://docs.docker.com/docker-for-mac/install/)

## Getting up and running (Local development only)

These steps are necessary to make sure all configurations are set up correctly so that you can get the project running correctly.

### Creating networks & build container

First, create the necessary networks and build the project:

```bash
docker network create top_and_zaak_backend_bridge
docker network create zaken_network
docker compose -f docker-compose.local.yml build
```

### Starting the backend

Run the following to start the backend:

```bash
docker compose -f docker-compose.local.yml up
```

### Creating a superuser

For accessing the Django admin during local development you'll have to become a `superuser`. This user should have the same `email` and `username` as the one that will be auto-created by the SSO login.

Run the following command to either create the user, or make the existing one a superuser:

```bash
sh bin/setup_superuser.sh <email>
```

### Using local development authentication
To run the project with local Django authentication instead of OpenID Connect (OIDC), create a `.local.env` file with:

```bash
LOCAL_DEVELOPMENT_AUTHENTICATION=False
```

### Django admin & services

Visit the Admin at http://localhost:8081/admin/

Check the health page to see if all services are up and running:
http://localhost:8080/health

### Creating user groups

To create all necessary user groups run the following command:

```bash
bash bin/setup_user_groups.sh
```

## Running tests

Set LOCAL_DEVELOPMENT_AUTHENTICATION environment variable to True (default)

Run unit tests locally with:

```bash
docker compose -f docker-compose.local.yml run --rm zaak-gateway python manage.py test
```

To run tests for a specific module, add a path:

```bash
docker compose -f docker-compose.local.yml run --rm zaak-gateway python manage.py test apps/cases

```

Or a specific test:

```bash
docker compose -f docker-compose.local.yml exec -T zaak-gateway python manage.py test apps.addresses.tests.tests_models.AddressModelTest.test_can_create_address_with_bag_result_without_stadsdeel
```


## API documentation (Swagger)

You can access the documentation at:
http://localhost:8080/api/v1/swagger/

## Generating an access token

When the LOCAL_DEVELOPMENT_AUTHENTICATION environment variable is set to True, you can gain access easily in the Swagger documentation by executing the /api/v1/oidc-authenticate/ POST request.
You can use the 'access' token in the response:
Click on the 'Authorize' button in the top right corner of the page, and enter the given access token.
This allows you to execute the API endpoints in the page.
By default, the `local.user@dev.com` user doesn't have any roles assigned.
From the [admin interface](http://localhost:8080/admin/) you can either assign roles or make the user superuser.

## Enabling local development environment variables

Create a `.env.local` file, on the root of your project, and override the variables you need locally

Start your project with the newly created environment variables, like so:

```bash
docker compose -f docker-compose.local.yml --env-file .env.local up
```

## Enabling Keycloak authentication for a locally run zaken-frontend

Set `LOCAL_DEVELOPMENT_AUTHENTICATION` by adding it to a `.local.env` file:

```bash
LOCAL_DEVELOPMENT_AUTHENTICATION=False
```

## Generating Mock Data

You can generate mock data easily (from the API swagger environment) by executing the `/api/v1/generate-mock/` GET request.

## Update fixtures

Generate new fixtures json file:

```bash
docker compose -f docker-compose.local.yml run --rm zaak-gateway python manage.py dumpdata --indent 2 -o temp_fixture.json [app_name]

```

Now manually copy changes you need to the corresponding fixtures file.

## Adding pre-commit hooks

You can add pre-commit hooks for checking and cleaning up your changes:

```bash
bash bin/install_pre_commit.sh
```

You can also run the following command to ensure all files adhere to coding conventions:

```bash
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
docker compose run --rm zaak-gateway python manage.py graph_models cases debriefings permits fines addresses events visits summons -X ModelEventEmitter,ModelEditableTimeConstraint,ModelEditablelBase --pygraphviz -o diagram.png
```

Note that the apps and models should be updated whenever applications and models are added or modified.

## Django DB migrations

For changes to the model you have to migrate the DB.

```bash
python manage.py makemigrations --name <name_of_your_migration> <name_of_apps>

python manage.py migrate
```

name_of_apps is the model you would like to change like: cases, events, workflow or schedules.
You can use the `---empty` flag to create a custom migration.

# FAQ

_Error: Account locked: too many login attempts. Contact an admin to unlock your account._

Cause: somebody tried to login with too many failed attempts. Unfortunately we have not
configured Axes properly so if one user does this, every user is locked.

Resolution: SSH into the webserver and run `python manage.py axes_reset`

# BPMN-Modelling

Try the online modeler for BPMN-models: https://bpmn.io/. This is a lightweight version for viewing a model.

## Editing models

Go to the releases page of the Camunda modeler: https://github.com/camunda/camunda-modeler/releases/ and download the appropriate zip. Extract the zip and start the Camunda Modeler. In the new versions of Camunda (v8) the form elements have been separated from the model. So use an older versio like v7 for example.

## NOTE: Making changes

When a new version is deployed, the already existing cases still follow the path in the started version. Only new created cases follow the path of the latest version.

When is it necessary to deploy a new version?

- Path changes in the model
- Timer changes
- ID changes

When is it NOT necessary to create a new version?

- Changes in form names. If you want to change the text of a form, you can do it directly in the latest version. Do not change IDs because paths can be taken based on an answer (ID).

So if you think existing cases are getting stuck in the model, just create a new version.

**NOTE:** When creating new routes **always use a default route**. If you made a mistake with versioning and new routes that do not exist in old versions, the application will follow the default route. If not, the application will colapse and celery workers will be unavailable.


## Versioning

The `director` model is the backbone of the BPMN-models. Watch out when updating the `director`! The `director` starts other models and ends them. The `director` chooses the applicable version of the model by the `director`'s major version itself. Example: a case has `director` version `6.0.0` and the `director` has to start the `unoccupied` model. The `unoccupied` model has versions: `4.0.0`, `4.0.1` and `7.1.0` (which shouldn't be possible). The `director` will choose `4.0.1` because it's the latest release of the `unoccupied` model with major version `6` or lower.

A new model can **NEVER have a higher major version than the `director`**.


## DIRECTOR changes major versioning

The **major version** of the `director` needs to be bumped if a route in the `director` to a new model has been added or updated. For example: a visit type changed in the `visit` model. In the `director` you can choose the visit type. Works like a charm for new cases. Existing cases use the old `director` and will be lead to the new `visit` model where the visit type condition has changed. Conditions are not met and the application will go down.


## Deploy new BPMN-model with incremented version

- Create a new version of the model file (.bpmn) in a new directory.
- The name of the directory should be the GLOBAL next version.

    Example: `housing_corporation` has a new minor version model and the latest version was `5.0.0` but the `director` has latest version `6.1.0`. Then the new minor version of `housing_corporation` will be `6.0.0`. The `director` with major version `6` will always start the latest `minor` version `6.0.0`.

```
bpmn_models/default/
├─ director/
│  ├─ 0.1.0/
│  ├─ 0.2.0/
│  ├─ 6.0.0/
│  ├─ 6.1.0/
├─ housing_coorporation/
│  ├─ 5.0.0/
│  │  ├─ housing_corporation.bpmn
│  ├─ 6.0.0/
│  │  ├─ housing_corporation.bpmn (NEW VERSION)
```

- Add the new version to `WORKFLOW_SPEC_CONFIG` in `settings.py`:

```json
"housing_corporation": {
    "versions": {
        "5.0.0": {},
        "6.0.0": {},  (NEW VERSION)
    },
}
```

- Run `docker compose build` to see your changes locally. Check the admin panel to see which `case workflow` version is used.

## Important learnings

### Forms
- Forms must be of type "Embedded or External Task Forms". If this is not possible add a `camunda:formKey="my_form_key"` to the `<bpmn:userTask/>`.

### User tasks
- ADDING a user_task to the model: it must be created as a class in user_tasks.py as well. The ID of the User task must match with the _task_name of the class.
- DELETING a user_task from the model: do NOT immediately remove it from user_tasks.py There may be an old version of this model running in production that needs this user_task. Removing this user_task will then create an error.

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

First, make sure you have built the project and executed the database migrations:

```
docker network create top_and_zaak_backend_bridge
docker network create zaken_network
docker compose build
```

Start AZA backend:

```
docker compose up
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

Visit the Admin at http://localhost:8080/admin/

Check the health page to see if all services are up and running:
http://localhost:8080/health

## Running tests

Set LOCAL_DEVELOPMENT_AUTHENTICATION environment variable to True (default)

Run unit tests locally with:

```
docker compose run --rm zaak-gateway python manage.py test
```

To run tests for a specific module, add a path:

```
docker compose run --rm zaak-gateway python manage.py test apps/cases
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

```
docker compose --env-file .env.local up
```

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

## Django DB migrations

For changes to the model you have to migrate the DB.

```python
python manage.py makemigrations --name name_of_your_migration

python manage.py migrate
```

# FAQ

_Error: Account locked: too many login attempts. Contact an admin to unlock your account._

Cause: somebody tried to login with too many failed attempts. Unfortunately we have not
configured Axes properly so if one user does this, every user is locked.

Resolution: SSH into the webserver and run `python manage.py axes_reset`

# BPMN-Modelling

Try the online modeler for BPMN-models: https://bpmn.io/. This is a lightweight version for viewing a model.

## Editing models

Clone the bpmn-io Github repo for editing: https://github.com/bpmn-io/bpmn-js-examples.

```
git clone git@github.com:bpmn-io/bpmn-js-examples.git
```

If you'd like to use Camunda Platform execution related properties, include the camunda-bpmn-moddle dependency which tells the modeler about camunda:XXX extension properties: https://github.com/bpmn-io/bpmn-js-examples/tree/master/properties-panel#camunda-platform

Follow next steps:
```
cd bpmn-js-examples

cd properties-panel

npm install camunda-bpmn-moddle
```

Then, you need to pass the respective properties provider together with the moddle extension to the modeler:

```js
import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
  CamundaPlatformPropertiesProviderModule
} from 'bpmn-js-properties-panel';

import CamundaBpmnModdle from 'camunda-bpmn-moddle/resources/camunda.json'

const bpmnModeler = new BpmnModeler({
  container: '#js-canvas',
  propertiesPanel: {
    parent: '#js-properties-panel'
  },
  additionalModules: [
    BpmnPropertiesPanelModule,
    BpmnPropertiesProviderModule,
    CamundaPlatformPropertiesProviderModule
  ],
  moddleExtensions: {
    camunda: CamundaBpmnModdle
  }
});
```

Finally:
```
npm run dev
```
Open `public/index.html` in your browser.

## NOTE: Making changes

When a new version is deployed, the already existing cases still follow the path in the started version. Only new created cases follow the path of the latest version.

When should you deploy a new version??

- Path changes in the model
- Timer changes
- ID changes

When should you NOT deploy a new version??

- Changes in form names. If you want to change the text of a form, you can do it directly in the latest version. Do not change IDs because paths can be taken based on the answer (ID).

So if you think existing cases will get stuck in the model, just create a new version to be sure.


## Deploy new BPMN-model with incremented version

- Create a new version of the model file (.bpmn) in a new directory.
- The name of the directory should be the GLOBAL next version.

    Example: `housing_corporation` has a new minor version model and the latest version was `5.0.0` but `debrief` has latest version `6.0.0`. Then the new minor version of `housing_corporation` will be `6.1.0`.

```
bpmn_models/default/
├─ debrief/
│  ├─ 0.1.0/
│  ├─ 0.2.0/
│  ├─ 6.0.0/
├─ housing_coorporation/
│  ├─ 5.0.0/
│  │  ├─ housing_corporation.bpmn
│  ├─ 6.1.0/
│  │  ├─ housing_corporation.bpmn
```

- Add the new version to `WORKFLOW_SPEC_CONFIG` in `settings.py`:

```python
"housing_corporation": {
    "versions": {
        "5.0.0": {},
        "6.1.0": {},
    },
}
```

Run `docker compose build` to see your changes locally. Check the admin panel to see which `case workflow` version is used.

## Important learnings

### Forms
- Forms must be of type "Embedded or External Task Forms". If this is not possible add a `camunda:formKey="my_form_key"` to the `<bpmn:userTask/>`.

### User tasks
- ADDING a user_task to the model: it must be created as a class in user_tasks.py as well. The ID of the User task must match with the _task_name of the class.
- DELETING a user_task from the model: do NOT immediately remove it from user_tasks.py There may be an old version of this model running in production that needs this user_task. Removing this user_task will then create an error.

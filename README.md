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

## What is currently running?
For prototyping purposes we are running two containers. A Python Django container, and the Open-zaak container.

### Django backend gateway
This is a Django application serves as a gateway of the open-zaak container (and other API's).
It can be accessed through port 8080:
```
localhost:8080
```

### Open-zaak Container
This app can be used for experimenting with the open-zaak application, and can be accessed through port 8090:
```
localhost:8090
```

## Accessing the open-zaak admin
Run the following command and follow the steps to create a super user:
```
docker-compose run --rm openzaak.local python src/manage.py createsuperuser
```

Once you have created an account, you should be able to access the admin:
http://localhost:8090/admin/

### Configuration Auth Credentials
You need to configure authorization credentials so our Flask container can talk to Open Zaak.
In the open zaak admin add a credential by navigating to:

API Autorisaties -> Applicaties -> Applicatie Toevoegen

Add any label, and the following Client Credentials:
- Client ID: 'client'
- Secret: 'secret_key'
Make sure to check the 'Heeft alle autorisaties' box.

Note: These settings are for local development only!

Navigate to http://localhost:8080/api/v1/ and you should see a response.

## OpenAPI documentation
To view the API documentation and to test the endpoints, you can navigate to http://localhost:8080/api/v1/swagger/.

## Generating Mock Data
For our proof of concept, you can generate some mock data.
Navigate or do a GET request to http://localhost:8080/api/v1/generate-mock/ and the application will generate some data. (This might take some time)

## Coding conventions and style
You can add pre-commit hooks for checking and cleaning up your changes:
```
bash install.sh
```

You can also run the following command to ensure all files adhere to coding conventions:
```
bash cleanup.sh
```
This will autoformat your code, sort your imports and fix overal problems.

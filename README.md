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
For prototyping purposes we are running two containers. A simple Python Flask container, and the Open-zaak container. 

### Simple Flask Container
This is a simple Python application that can be used for experimenting, and can be accessed through port 8000: 
```
localhost:8000
```
It's easy to set up routes and views using this application (see app directory)

### Open-zaak Container
This app can be used for experimenting with the open-zaak application, and can be accessed through port 8080:
```
localhost:8080
```

## Accessing the open-zaak admin
Run the following command and follow the steps to create a super user:
```
docker-compose run --rm openzaak python src/manage.py createsuperuser
```

Once you have created an account, you should be able to access the admin:
http://localhost:8080/admin/

### Configuration Auth Credentials 
You need to configure authorization credentials so our Flask container can talk to Open Zaak.
In the open zaak admin add a credential by navigating to:

API Autorisaties -> Applicaties -> Applicatie Toevoegen

Add any label, and the following Client Credentials:
- Client ID: 'client'
- Secret: 'secret_key'
Make sure to check the 'Heeft alle autorisaties' box.

Note: These settings are for local development only! 

Navigate to http://localhost:8000/ and you should see a response

### Generating Mock Data
For our proof of concept, you can generate some mock data.
Navigate or do a GET request to http://localhost:8000/generate-data and the application will generate some data.
(This might take a minute or two)

## Accessing data
Once the data is generated, you can request all data through: http://localhost:8000/
Authorisation is not required at this point, and is handled in the Flask backend.

Some of the response objects contain references to other objects. This reference is a unique url, and its data can be requested using a generic endpoint:
http://localhost:8000/object?url=OBJECT_URL

Replace OBJECT_URL with the object url you would like to request.
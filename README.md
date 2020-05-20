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
0.0.0.0:8000
```
It's easy to set up routes and views using this application (see app directory)

### Open-zaak Container
This app can be used for experimenting with the open-zaak application, and can be accessed through port 8080:
```
0.0.0.0:8080
```

## Accessing the open-zaak admin
Run the following command and follow the steps to create a super user:
```
docker-compose run --rm openzaak python src/manage.py createsuperuser
```

Once you have created an account, you should be able to access the admin:
http://localhost:8080/admin/

# Test script for the backend API

## Todo

- Taak opvoeren?
- Visit: should be Top-Task?
- Do we need CitizenReport?

## Installing

You can install in a virtualenv.

```
virtualenv env
. env/bin/activate
pip install -r requirements.txt
```

## Running the test

Follow install instructions from the main README.md file.
And make sure we have the right database configuration.

```
docker-compose -f ../docker-compose.test.yml build
docker-compose run --rm zaak-gateway python manage.py migrate
bash ../bin/setup_credentials.sh
./fix_models.sh
```

Now start Docker with the test config file and run the test suite.

```
docker-compose -f ../docker-compose.test.yml up
LOGLEVEL=INFO NO_SKIP=1 nose2
```

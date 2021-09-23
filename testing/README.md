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

Start Docker with the test config file.

```
docker-compose -f ../docker-compose.test.yml up -d
```

Make sure we have the correct SummonTypes in our db.
Create a new summon-type for CLOSING

    (camunda_option=sluiting, name=sluiting, theme=1, id=13)
    (camunda_option=legalisatie-brief, name=legalisatie-brief, theme=1)

Now run the test suite

```
LEGACY=1 nose2
```

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

Start Docker with the test config file and make sure we have the right SummonTypes.

```shell
docker-compose -f ../docker-compose.test.yml up -d
docker-compose run zaak-gateway python manage.py shell -c "from apps.summons.models import SummonType; type = SummonType.objects.get(pk=13); type.camunda_option='sluiting'; type.save(); SummonType.objects.get_or_create(camunda_option='legalisatie-brief', name='Legalisatie-brief', theme_id=1)"
```

Now run the test suite

```
nose2
```

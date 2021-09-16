# Test script for the backend API

## Installing

You can install in a virtualenv.

```
virtualenv env
. env/bin/activate
pip install -r requirements.txt
```

## Running the test

```
docker-compose -f ../docker-compose.test.yml up -d
python -m unittest
```

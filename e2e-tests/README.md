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
Now start Docker with the test config file and run the test suite.

```
./setup_or_reset_and_start.sh
```

LOGLEVEL=INFO NO_SKIP=1 nose2

```

```

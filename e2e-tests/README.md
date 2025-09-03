# Test script for the backend API

## Todo

- Taak opvoeren?
- Visit: should be Top-Task?
- Do we need CitizenReport?

## Installing

You can install via Poetry.

```
poetry install
```

## Running the test

Follow install instructions from the main README.md file.
And make sure we have the right database configuration.
Now start Docker with the test config file and run the test suite.

```sh
./setup_or_reset_and_start.sh
```

```sh
LOGLEVEL=INFO NO_SKIP=1 nose2
```

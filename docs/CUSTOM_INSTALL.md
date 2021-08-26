# Custom (minimal) install

_Please note; this is experimental_

TODO:

- remove pg_trgm

_Install and create database and user_

```
brew install postgres
bin/setup_postgres.sh
cp .env.local.dist .env.local
```

_Install the app_

```
cd app
virtualenv env
. env/bin/activate
pip install -r requirements.txt
python local.py migrate
../bin/setup_postgres_credentials.sh
```

_Start the app_

```
python local.py runserver localhost:8080
```

_If you need Camunda too_

Build the Camunda container and create the database:

```
docker build -t camunda-ritense ../camunda/deployment
createdb process_engine
```

Start the container:

```
docker run -p 7000:8080 \
    -e DB_URL=jdbc:postgresql://host.docker.internal:5432/process_engine \
    --env-file ../camunda/.env camunda-ritense
```

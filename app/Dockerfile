FROM python:3.13-slim-trixie

ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

# Setup Certificates for ADP/Motiv
COPY certificates/adp_rootca.crt /usr/local/share/ca-certificates/adp_rootca.crt
RUN chmod 644 /usr/local/share/ca-certificates/adp_rootca.crt \
    && update-ca-certificates --fresh

ENV PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=2.1

# Update and install necessary packages including GDAL
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    graphviz \
    graphviz-dev \
    postgresql-client \
    tzdata \
    wget \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip setuptools wheel pygraphviz uwsgi
RUN pip install "poetry==$POETRY_VERSION"

RUN echo "10.240.5.72     acc.api.data.amsterdam.nl" >> /etc/hosts || echo "Could not write to /etc/hosts"

WORKDIR /app

COPY pyproject.toml poetry.lock  ./
RUN poetry install --no-interaction --no-ansi --only main

COPY . /app/

RUN chmod +x /app/restore_db.sh
RUN chmod +x /app/wait-for.sh
RUN chmod +x /app/celery.sh
RUN chmod +x /app/deploy/docker-entrypoint.sh

# Set the GDAL_LIBRARY_PATH environment variable
ENV GDAL_LIBRARY_PATH /usr/lib/libgdal.so

ENTRYPOINT ["/app/deploy/docker-entrypoint.sh"]
CMD ["uwsgi", "--ini", "/app/deploy/config.ini"]

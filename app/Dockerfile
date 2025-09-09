FROM python:3.13-slim-trixie

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VERSION=2.1.4

# -------------------------------------------------------------------
# UTF-8 configuration
# -------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
    && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
    && locale-gen \
    && rm -rf /var/lib/apt/lists/*
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8
# -------------------------------------------------------------------

# Setup Certificates for ADP/Motiv
COPY certificates/adp_rootca.crt /usr/local/share/ca-certificates/adp_rootca.crt
RUN chmod 644 /usr/local/share/ca-certificates/adp_rootca.crt \
    && update-ca-certificates --fresh

# Install other dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    graphviz \
    graphviz-dev \
    postgresql-client \
    tzdata \
    media-types \
    wget \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel pygraphviz uwsgi
RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

# Install project dependencies via Poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --only main

# Copy application code
COPY . /app/

# Make scripts executable
RUN chmod +x /app/restore_db.sh \
    && chmod +x /app/wait-for.sh \
    && chmod +x /app/celery.sh \
    && chmod +x /app/deploy/docker-entrypoint.sh

# Set the GDAL_LIBRARY_PATH environment variable
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so

ENTRYPOINT ["/app/deploy/docker-entrypoint.sh"]
CMD ["uwsgi", "--ini", "/app/deploy/config.ini"]

FROM python:3.10-bullseye

ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

# Setup Certificates for ADP/Motiv
COPY certificates/adp_rootca.crt /usr/local/share/ca-certificates/adp_rootca.crt
RUN chmod 644 /usr/local/share/ca-certificates/adp_rootca.crt \
    && update-ca-certificates --fresh

ENV PYTHONUNBUFFERED 1

# Update and install necessary packages including GDAL
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    graphviz \
    graphviz-dev \
    postgresql-client

RUN pip install --upgrade pip setuptools wheel
RUN pip install uwsgi
RUN pip install pygraphviz

RUN echo "10.240.5.72     acc.api.data.amsterdam.nl" >> /etc/hosts || echo "Could not write to /etc/hosts"

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/

RUN chmod +x /app/restore_db.sh
RUN chmod +x /app/wait-for.sh
RUN chmod +x /app/celery.sh
RUN chmod +x /app/deploy/docker-entrypoint.sh

# Set the GDAL_LIBRARY_PATH environment variable
ENV GDAL_LIBRARY_PATH /usr/lib/libgdal.so

ENTRYPOINT ["/app/deploy/docker-entrypoint.sh"]
CMD ["uwsgi", "--ini", "/app/deploy/config.ini"]

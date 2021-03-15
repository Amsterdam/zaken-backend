FROM amsterdam/python
LABEL maintainer="datapunt@amsterdam.nl"

ENV REQUESTS_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt

# Setup Certificates for ADP/Motiv
ADD certificates/adp_rootca.crt /usr/local/share/ca-certificates/adp_rootca.crt
RUN chmod 644 /usr/local/share/ca-certificates/adp_rootca.crt \
  && update-ca-certificates --fresh

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y
RUN pip install --upgrade pip
RUN pip install uwsgi

RUN apt-get install graphviz graphviz-dev -y
RUN pip install pygraphviz

RUN echo "10.240.5.72     acc.api.data.amsterdam.nl" >> /etc/hosts

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/

RUN chmod +x /app/wait-for.sh
RUN chmod +x /app/celery.sh
RUN chmod +x /app/deploy/docker-entrypoint.sh

CMD ["bash", "/app/deploy/docker-entrypoint.sh"]

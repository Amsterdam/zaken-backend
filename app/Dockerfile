FROM amsterdam/python

MAINTAINER datapunt@amsterdam.nl

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y
RUN pip install --upgrade pip
RUN pip install uwsgi

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app/

#RUN python manage.py migrate
RUN mkdir -p /static && chown datapunt /static
RUN python manage.py collectstatic --no-input

CMD cd /app/app/ && uwsgi --http-socket 0.0.0.0:8000 --mount /=config.wsgi:application --py-auto-reload=1
from django.core.wsgi import get_wsgi_application

from .logging import start_logging

start_logging()
application = get_wsgi_application()

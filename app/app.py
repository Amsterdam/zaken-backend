# Very experimental proof of concept for a simple flask app and a connected open-zaak app

import time
import requests
from flask import Flask, Response

app = Flask(__name__)

CASES_PATH = 'http://openzaak:8000'
STATIC_PATH = 'static-sub/static'

@app.route('/test')
def hello():
    return 'Hello World! {}'.format(time.time())

@app.route('/')
def cases():
    return requests.get(CASES_PATH).text

@app.route('/{}/<path:path>'.format(STATIC_PATH))
def static_files(path):
    path = '{}/{}/{}'.format(CASES_PATH, STATIC_PATH, path)
    r = requests.get(path)
    return Response(response=r.text, status=r.status_code, content_type=r.headers.get('content-type', ''))

@app.route('/<path:path>')
def cases_sub(path):
    path = '{}/{}'.format(CASES_PATH, path)
    return requests.get(path).text

@app.route('/health')
def health_check():
    """
    A tentative health check
    """
    return 'Connectivity OK'

if __name__ == '__main__':  # pragma: no cover
    app.run()
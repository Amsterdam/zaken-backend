import time

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():

    return 'Hello World! {}'.format(time.time())
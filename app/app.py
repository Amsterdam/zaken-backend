import time

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World! {}'.format(time.time())


if __name__ == '__main__':  # pragma: no cover
    app.run()
import time
from flask import Flask

from services.service_catalogs import create_catalog, get_catalogs
from services.service_case_types import create_case_type, get_case_types
from services.service_state_types import create_state_types, get_state_types

app = Flask(__name__)

@app.route('/')
def index():
    catalogs = get_catalogs()
    case_types = get_case_types()
    state_types = get_state_types()

    return {
        'catalogs': catalogs,
        'case_types': case_types,
        'state_types': state_types
    }

@app.route('/generate_data')
def generate_data():
    catalog = create_catalog()
    case_type = create_case_type(catalog['url'])
    state_types = create_state_types(case_type['url'])

    return {
        'catalog': catalog,
        'case_type': case_type,
        'state_types': state_types
    }

@app.route('/health')
def health_check():
    """
    A tentative health check
    """
    return 'Connectivity OK'

if __name__ == '__main__':  # pragma: no cover
    app.run()

import time
from flask import Flask

from services.service_catalogs import create_catalog, get_catalogs
from services.service_case_types import create_case_type, get_case_types, delete_case_type, publish_case_type
from services.service_state_types import create_state_types, get_state_types
from services.service_cases import get_cases, create_case

app = Flask(__name__)

@app.route('/')
def index():
    catalogs = get_catalogs()
    case_types = get_case_types()
    state_types = get_state_types()
    cases = get_cases()

    return {
        'catalogs': catalogs,
        'case_types': case_types,
        'state_types': state_types,
        'cases': cases
    }

@app.route('/generate_data')
def generate_data():
    catalog = create_catalog()
    case_type = create_case_type(catalog['url'])
    state_types = create_state_types(case_type['url'])
    publish_case_type(case_type['url'])
    case = create_case(case_type['url'])

    return {
        'catalog': catalog,
        'case_type': case_type,
        'state_types': state_types,
        'case': case
    }


@app.route('/generate_case')
def generate_case():
    case_types = get_case_types()
    case_type = case_types['results'][0]
    case = create_case(case_type['url'])

    return {
        'case': case
    }



@app.route('/delete_data')
def delete_data():
    responses = []
    case_types = get_case_types()['results']

    for case_type in case_types:
        url = case_type['url']
        response = delete_case_type(url)
        responses.append(response)

    return {
        'responses': responses
    }

@app.route('/health')
def health_check():
    """
    A tentative health check
    """
    return 'Connectivity OK'

if __name__ == '__main__':  # pragma: no cover
    app.run()

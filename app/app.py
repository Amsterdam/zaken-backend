import random
from flask import Flask
from flask import request

from services.service_catalogs import get_catalogs, get_or_create_catalog
from services.service_case_types import create_case_type, get_case_types, delete_case_type, publish_case_type
from services.service_state_types import create_state_types, get_state_types
from services.service_cases import get_cases, create_case
from services.service_states import add_state_to_case
from services.service_objects import get_object
from services.service_case_objects import add_bag_object_to_case, get_case_objects

app = Flask(__name__)

@app.route('/')
def display_data():
    catalogs = get_catalogs()
    case_types = get_case_types()
    state_types = get_state_types()
    cases = get_cases()
    case_objects = get_case_objects()

    return {
        'catalogs': catalogs,
        'case_types': case_types,
        'state_types': state_types,
        'cases': cases,
        'cases_objects': case_objects
    }

@app.route('/generate-data')
def generate_data():
    delete_data()

    catalog = get_or_create_catalog()
    case_type = create_case_type(catalog['url'])
    state_types = create_state_types(case_type['url'])
    publish_case_type(case_type['url'])

    for i in range(0,10):
        generate_case()

    return display_data()

@app.route('/generate-case')
def generate_case():
    # First create the case
    case_types = get_case_types()
    case_type = case_types['results'][0]
    case = create_case(case_type['url'])

    # Add a random state
    state_types = get_state_types()['results']
    state_type = random.choice(state_types)
    state = add_state_to_case(case['url'], state_type['url'])

    # Add a BAG object
    bag_url = 'https://api.data.amsterdam.nl/bag/v1.1/nummeraanduiding/0363200012086033/'
    add_bag_object_to_case(case['url'], bag_url)

    return {
        'case': case,
        'state': state
    }

@app.route('/delete-data')
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

@app.route('/object')
def object_detail():
    object_url = request.args.get('url', None)
    if object_url:
        return get_object(object_url)

    return {
        'error': 'No object url specified'
    }

@app.route('/health')
def health_check():
    """
    A tentative health check
    """
    return 'Connectivity OK'

if __name__ == '__main__':  # pragma: no cover
    app.run()

import requests
import jwt
import json
from services.settings import CONNECTIONS
from datetime import datetime

class Connection:
    def __init__(self, connection_name):
        connection_settings = CONNECTIONS[connection_name]
        self.host = connection_settings['host']
        self.port = connection_settings['port']
        self.api_version = connection_settings['api_version']
        self.secret_key = connection_settings['secret_key']
        self.client = connection_settings['client']

    def get_data(self, domain, data_type):
        request_method = requests.get
        return self.__do_request__(domain, data_type, request_method)

    def post_data(self, domain, data_type, data):
        request_method = requests.post
        return self.__do_request__(domain, data_type, request_method, data)

    def __get_header__(self, token):
        headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {}'.format(token)
        }
        return headers

    def __get_token__(self, key, client):
        token = jwt.encode(
            headers={ 'client_identifier': client},
            payload={
                'iss': client,
                'iat': datetime.utcnow(),
                'client_id': client,
                'user_id': '',
                'user_representation': '',
            },
            key=key)

        return str(token, 'utf-8')

    def __get_path__(self, sub_path, data_type):
        path = 'http://{}:{}/{}/api/{}/{}'.format(self.host, self.port, sub_path, self.api_version, data_type)
        return path

    def __do_request__(self, domain, data_type, request_method, data=None):
        path = self.__get_path__(domain, data_type)
        token = self.__get_token__(self.secret_key, self.client)
        headers = self.__get_header__(token)
        try:
            response = request_method(path, headers=headers, json=data)
            return response.json()
        except Exception as e:
            print(e)

class Service:
    def __init__(self, name, types, connection):
        self.name = name
        self.types = types
        self.connection = connection

    def get(self, data_type):
        try:
            assert  data_type in self.types, 'Data type is not compatible with this domain'
        except Exception as e:
            return {'message': str(e)}

        return self.connection.get_data(self.name, data_type)

    def post(self, data_type, data):
        try:
            assert data_type in self.types, 'Data type is not compatible with this domain'
            assert data, 'Data is not available'
            assert json.dumps(data), 'Data should be valid JSON'
        except Exception as e:
            return {'message': str(e)}

        return self.connection.post_data(self.name, data_type, data)

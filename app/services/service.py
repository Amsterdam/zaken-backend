import json
from datetime import datetime

import jwt
import requests

from services.settings import CONNECTIONS


class Connection:
    def __init__(self, connection_name):
        connection_settings = CONNECTIONS[connection_name]
        self.host = connection_settings['host']
        self.port = connection_settings['port']
        self.api_version = connection_settings['api_version']
        self.secret_key = connection_settings['secret_key']
        self.client = connection_settings['client']

    def get_data(self, domain, data_type, pk=None):
        request_method = requests.get
        return self.__do_request__(domain, data_type, request_method, pk)

    def post_data(self, domain, data_type, data):
        request_method = requests.post
        return self.__do_request__(domain, data_type, request_method, data)

    def get(self, object_url):
        token = self.__get_token__(self.secret_key, self.client)
        headers = self.__get_header__(token)
        return self.__request__(object_url, headers, requests.get)

    def publish(self, object_url):
        path = '{}/publish'.format(object_url)
        token = self.__get_token__(self.secret_key, self.client)
        headers = self.__get_header__(token)
        return self.__request__(path, headers, requests.post)

    def delete(self, object_url):
        token = self.__get_token__(self.secret_key, self.client)
        headers = self.__get_header__(token)
        return self.__request__(object_url, headers, requests.delete)

    def __get_header__(self, token):
        headers = {
            'accept': 'application/json',
            'Authorization': 'Bearer {}'.format(token),
            'Accept-Crs': 'EPSG:4326',
            'Content-Crs': 'EPSG:4326',
        }
        return headers

    def __get_token__(self, key, client):
        token = jwt.encode(
            headers={'client_identifier': client},
            payload={
                'iss': client,
                'iat': datetime.utcnow(),
                'client_id': client,
                'user_id': '',
                'user_representation': '',
            },
            key=key)

        return str(token, 'utf-8')

    def __get_path__(self, sub_path, data_type, pk=None):
        path = 'http://{}:{}/{}/api/{}/{}'.format(self.host, self.port, sub_path, self.api_version, data_type)
        if pk:
            path = '{}/{}'.format(path, pk)
        return path

    def __do_request__(self, domain, data_type, request_method, pk=None, data=None):
        path = self.__get_path__(domain, data_type, pk)
        token = self.__get_token__(self.secret_key, self.client)
        headers = self.__get_header__(token)
        return self.__request__(path, headers, request_method, data)

    def __request__(self, path, headers, request_method, data=None):
        try:
            response = request_method(path, headers=headers, json=data)
            return response.json()
        except Exception as e:
            return e


class Service:

    def __init__(self, name, types, connection):
        self.name = name
        self.types = types
        self.connection = connection

    def get(self, data_type):
        try:
            assert data_type in self.types, 'Data type is not compatible with this domain'
        except Exception as e:
            return {'message': str(e)}

        return self.connection.get_data(self.name, data_type)

    def get_detail(self, data_type, pk):
        try:
            assert data_type in self.types, 'Data type is not compatible with this domain'
        except Exception as e:
            return {'message': str(e)}

        return self.connection.get_data(self.name, data_type, pk)

    def post(self, data_type, data):
        try:
            assert data_type in self.types, 'Data type is not compatible with this domain'
            assert data, 'Data is not available'
            assert json.dumps(data), 'Data should be valid JSON'
        except Exception as e:
            return {'message': str(e)}

        return self.connection.post_data(self.name, data_type, data)

    def publish(self, object_url):
        return self.connection.publish(object_url)

    def delete(self, object_url):
        return self.connection.delete(object_url)


def create_connection(connection_host):
    connection = Connection(connection_host)
    return connection


def create_service(connection_host, domain, sub_domains):
    connection = create_connection(connection_host)
    service = Service(domain, sub_domains, connection)
    return service

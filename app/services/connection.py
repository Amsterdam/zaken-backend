from datetime import datetime
import jwt
import requests

from services.settings import CONNECTIONS


class Connection:
    def __init__(self, connection_name, domain, data_type):
        connection_settings = CONNECTIONS[connection_name]
        self.host = connection_settings['host']
        self.port = connection_settings['port']
        self.api_version = connection_settings['api_version']
        self.secret_key = connection_settings['secret_key']
        self.client = connection_settings['client']

        self.domain = domain
        self.data_type = data_type

    def get(self, pk=None):
        request_method = requests.get
        path = self.__get_path__(pk)
        return self.__request__(path, request_method)

    def post(self, pk=None):
        request_method = requests.post
        path = self.__get_path__(pk)
        return self.__request__(path, request_method)

    def put(self, pk=None):
        request_method = requests.put
        path = self.__get_path__(pk)
        return self.__request__(path, request_method)

    def patch(self, pk=None):
        request_method = requests.patch
        path = self.__get_path__(pk)
        return self.__request__(path, request_method)

    def delete(self, pk=None):
        request_method = requests.delete
        path = self.__get_path__(pk)
        return self.__request__(path, request_method)

    def publish(self, pk=None):
        request_method = requests.publish
        path = self.__get_path__(pk, publish=True)
        return self.__request__(path, request_method)

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

    def __get_path__(self, pk=None, publish=False):
        path = 'http://{}:{}/{}/api/{}/{}'.format(self.host, self.port, self.domain, self.api_version, self.data_type)
        if pk:
            path = '{}/{}'.format(path, pk)

        if publish:
            path = '{}/publish'.format(path)

        return path

    def __request__(self, path, request_method, data=None):
        token = self.__get_token__(self.secret_key, self.client)
        headers = self.__get_header__(token)

        try:
            response = request_method(path, headers=headers, json=data)
            print(response)
            print('XXXXXX')
            print(response.json())
            return response.json()
        except Exception as e:
            return e
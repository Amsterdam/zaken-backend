from datetime import datetime

import jwt
import requests
from rest_framework.exceptions import APIException
from services.settings import CONNECTIONS


class Connection:
    def __init__(self, connection_name, domain, data_type):
        connection_settings = CONNECTIONS[connection_name]
        self.host = connection_settings["host"]
        self.port = connection_settings["port"]
        self.api_version = connection_settings["api_version"]
        self.secret_key = connection_settings["secret_key"]
        self.client = connection_settings["client"]

        self.domain = domain
        self.data_type = data_type

    def get_url(self, url):
        request_method = requests.get
        response = self.__request__(url, request_method)
        return response.json()

    def get(self, uuid=None, params=None):
        request_method = requests.get
        path = self.__get_path__(uuid=uuid)
        response = self.__request__(path, request_method, params=params)
        return response.json()

    def post(self, uuid=None, data={}):
        request_method = requests.post
        path = self.__get_path__(uuid)
        response = self.__request__(path, request_method, data)
        return response.json()

    def put(self, uuid=None, data={}):
        request_method = requests.put
        path = self.__get_path__(uuid)
        response = self.__request__(path, request_method, data)
        return response.json()

    def patch(self, uuid=None, data={}):
        request_method = requests.patch
        path = self.__get_path__(uuid)
        response = self.__request__(path, request_method, data)
        return response.json()

    def delete(self, uuid=None):
        request_method = requests.delete
        path = self.__get_path__(uuid)
        response = self.__request__(path, request_method)
        return response

    def publish(self, uuid=None):
        request_method = requests.post
        path = self.__get_path__(uuid, publish=True)
        response = self.__request__(path, request_method)
        return response.json()

    def __get_header__(self, token):
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer {}".format(token),
            "Accept-Crs": "EPSG:4326",
            "Content-Crs": "EPSG:4326",
        }
        return headers

    def __get_token__(self, key, client):
        token = jwt.encode(
            headers={"client_identifier": client},
            payload={
                "iss": client,
                "iat": datetime.utcnow(),
                "client_id": client,
                "user_id": "",
                "user_representation": "",
            },
            key=key,
        )

        return token

    def __get_path__(self, uuid=None, publish=False):
        if self.port:
            path = f"http://{self.host}:{self.port}/{self.domain}/api/{self.api_version}/{self.data_type}"
        else:
            path = f"https://{self.host}/{self.domain}/api/{self.api_version}/{self.data_type}"

        if uuid:
            path = f"{path}/{uuid}"

        if publish:
            path = f"{path}/publish"

        return path

    def __request__(self, path, request_method, data=None, params=None):
        token = self.__get_token__(self.secret_key, self.client)
        headers = self.__get_header__(token)

        try:
            response = request_method(path, headers=headers, json=data, params=params)
            response.raise_for_status()
        except Exception as e:
            raise APIException(f"Path: {path} Error:{str(e)}")

        return response

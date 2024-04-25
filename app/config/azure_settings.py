import os
import shlex
import subprocess
from subprocess import PIPE

from azure.identity import DefaultAzureCredential, WorkloadIdentityCredential


class AzureAuth:
    def __init__(self):
        self._credential = None

    @property
    def credential(self):
        if not self._credential:
            self._credential = self.get_credential()

        return self._credential

    def get_credential(self):
        credential = None
        federated_token_file = os.getenv("AZURE_FEDERATED_TOKEN_FILE")
        if federated_token_file:
            # This relies on environment variables that get injected.
            # AZURE_AUTHORITY_HOST:       (Injected by the webhook)
            # AZURE_CLIENT_ID:            (Injected by the webhook)
            # AZURE_TENANT_ID:            (Injected by the webhook)
            # AZURE_FEDERATED_TOKEN_FILE: (Injected by the webhook)
            credential = WorkloadIdentityCredential()
        elif os.isatty(0):
            account = subprocess.run(
                shlex.split("az account show"),
                check=False,
                stdout=PIPE,
                stderr=PIPE,
            )
            if account.returncode != 0:
                subprocess.run(
                    shlex.split("az login"),
                    check=True,
                    stdout=PIPE,
                )

            credential = DefaultAzureCredential(managed_identity_client_id=None)
        else:
            raise Exception("cannot connect to azure")

        return credential

    @property
    def db_password(self) -> object:
        # return access_token.token
        class DynamicString:
            def __init__(self, credential, scopes) -> None:
                self.credential = credential
                self.scopes = scopes

            def __str__(self):
                access_token = self.credential.get_token(*self.scopes)
                return access_token.token

        scopes = ["https://ossrdbms-aad.database.windows.net/.default"]
        return DynamicString(self.credential, scopes)


class Azure:
    def __init__(self) -> None:
        self.auth = AzureAuth()

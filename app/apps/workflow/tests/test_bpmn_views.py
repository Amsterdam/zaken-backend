from apps.workflow.utils import get_bpmn_model_versions_and_files, get_bpmn_models
from django.core import management
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from utils.unittest_helpers import get_authenticated_client, get_unauthenticated_client


class BpmnModelsApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def get_versions_url(self, model_name):
        return reverse(
            "bpmn-models-get-model-versions", kwargs={"model_name": model_name}
        )

    def get_file_url(self, model_name, version):
        return reverse(
            "bpmn-models-get-bpmn-file",
            kwargs={"model_name": model_name, "version": version},
        )

    def test_unauthenticated_get(self):
        client = get_unauthenticated_client()

        for url in (
            reverse("bpmn-models-list"),
            self.get_versions_url("director"),
            self.get_file_url("director", "0.1.0"),
        ):
            response = client.get(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_model_names(self):
        response = get_authenticated_client().get(reverse("bpmn-models-list"))
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data, sorted(data))
        self.assertIn("director", data)
        self.assertIn("sub_workflow", data)

    def test_model_versions(self):
        response = get_authenticated_client().get(self.get_versions_url("director"))
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            data[0],
            {"version": "0.1.0", "file_name": "director.bpmn", "model": "director"},
        )

    def test_model_versions_are_sorted_by_version(self):
        for model_name in get_bpmn_models():
            versions = [
                tuple(map(int, v["version"].split(".")))
                for v in get_bpmn_model_versions_and_files(model_name)
            ]
            self.assertTrue(versions)
            self.assertEqual(versions, sorted(versions))

    def test_model_versions_unknown_model(self):
        client = get_authenticated_client()

        for model_name in ("foo", ".."):
            response = client.get(f"/api/v1/bpmn-models/{model_name}/")
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bpmn_file(self):
        response = get_authenticated_client().get(
            self.get_file_url("director", "0.1.0")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/xml")
        self.assertIn("bpmn:definitions", response.content.decode())

    def test_bpmn_file_for_every_version(self):
        client = get_authenticated_client()

        for model_name in get_bpmn_models():
            for bpmn_model in get_bpmn_model_versions_and_files(model_name):
                response = client.get(
                    self.get_file_url(model_name, bpmn_model["version"])
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bpmn_file_unknown_model_or_version(self):
        client = get_authenticated_client()

        for path in (
            "foo/file/0.1.0",
            "director/file/99.99.99",
            "director/file/..",
            "../file/default",
        ):
            response = client.get(f"/api/v1/bpmn-models/{path}/")
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

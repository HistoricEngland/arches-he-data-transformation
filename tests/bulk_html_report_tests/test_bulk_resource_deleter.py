import os
import uuid

from arches.app.models import models
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory

from arches_he_data_transformation.etl_modules.bulk_resource_deleter import (
    BulkResourceDeleter,
)
from .base_test import BaseBulkHtmlTestCase


# These tests can be run from the command line via:
#     python manage.py test tests.bulk_html_report_tests.test_bulk_resource_deleter --settings="tests.test_settings"
# or if using Docker:
#     python manage.py test tests.bulk_html_report_tests.test_bulk_resource_deleter --settings="tests.test_settings_for_docker"


class TestBulkResourceDeleter(BaseBulkHtmlTestCase):
    def create_csv_file_request(self, file_path, file_name):
        rf = RequestFactory()
        with open(file_path, "rb") as f:
            upload = SimpleUploadedFile(file_name, f.read(), content_type="text/csv")

        post_data = {
            "module": "204e515a-a782-49e6-be98-6134e144468b",
            "load_id": "21186e24-e407-4726-adc3-6c5e259c06cd",
            "transaction_id": "6fc6d840-37f8-47df-a624-91412f63ec3f",
        }

        request = rf.post("/etl-manager", data={**post_data, "file": upload})
        request.user = self.admin
        request.load_id = post_data["load_id"]
        request.transaction_id = post_data["transaction_id"]
        return request

    def test_01_etl_module_exists(self):
        etl = models.ETLModule.objects.all()
        self.assertTrue(etl.filter(name="Bulk Resource Deleter").exists())

    def test_02_resourceids_can_be_read(self):
        csv_file_path = os.path.join("tests", "test_data", "test_data_csv_1.csv")
        request = self.create_csv_file_request(
            file_path=csv_file_path, file_name="test_data_csv_1.csv"
        )

        deleter = BulkResourceDeleter()
        result = deleter.read(request=request)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["data"]["resourceids"]["data"]), 2)

    def test_03_invalid_file_header(self):
        csv_file_path = os.path.join("tests", "test_data", "test_data_csv_2.csv")
        request = self.create_csv_file_request(
            file_path=csv_file_path, file_name="test_data_csv_2.csv"
        )

        deleter = BulkResourceDeleter()
        result = deleter.read(request=request)

        self.assertFalse(result["success"])
        self.assertEqual(
            result["data"],
            "Failed to read the values in your file due to incorrect headers.  Check you have a 'resourceinstanceid' or 'resourceid' column.",
        )

    def test_04_invalid_resource_value(self):
        csv_file_path = os.path.join("tests", "test_data", "test_data_csv_3.csv")
        request = self.create_csv_file_request(
            file_path=csv_file_path, file_name="test_data_csv_3.csv"
        )

        deleter = BulkResourceDeleter()
        result = deleter.read(request=request)

        self.assertFalse(result["success"])
        self.assertIn("is not a valid UUID", result["data"])

    def test_05_return_resource_values(self):
        csv_file_path = os.path.join("tests", "test_data", "test_data_csv_1.csv")
        request = self.create_csv_file_request(
            file_path=csv_file_path, file_name="test_data_csv_1.csv"
        )

        deleter = BulkResourceDeleter()
        result = deleter.get_resourceid_values(request=request)

        self.assertTrue(result["success"])
        self.assertEqual(
            result["data"],
            [
                "c5f82f01-e696-41f8-b86a-ec595282a1dc",
                "07c233eb-e674-48d0-9262-6ef3f25e4f44",
            ],
        )

    def test_06_run_bulk_delete_task_successfully_deletes_resources(self):
        csv_file_path = os.path.join("tests", "test_data", "test_data_csv_1.csv")
        request = self.create_csv_file_request(
            file_path=csv_file_path, file_name="test_data_csv_1.csv"
        )

        deleter = BulkResourceDeleter()
        read_result = deleter.read(request=request)
        self.assertTrue(read_result["success"])

        resourceids = read_result["data"]["resourceids"]["data"]
        load_id = str(uuid.uuid4())
        transaction_id = str(uuid.uuid4())

        # Ensure load event row exists for status updates inside delete flow.
        models.LoadEvent.objects.create(
            loadid=load_id,
            complete=False,
            status="validated",
            successful=None,
            etl_module_id=deleter.moduleid,
            user_id=self.admin.id,
        )

        deleter.run_bulk_delete_task(
            self.admin.id,
            load_id,
            resourceids,
            transaction_id,
        )

        remaining = models.ResourceInstance.objects.filter(
            resourceinstanceid__in=resourceids
        ).count()
        self.assertEqual(remaining, 0)

        delete_logs = models.EditLog.objects.filter(
            transactionid=transaction_id,
            edittype="delete",
            resourceinstanceid__in=resourceids,
        )

        distinct_deleted_resources = (
            delete_logs.values("resourceinstanceid").distinct().count()
        )
        self.assertEqual(distinct_deleted_resources, len(resourceids))

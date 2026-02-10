import os
import zipfile
from arches.app.models.graph import Graph
from arches.app.models import models
from django.contrib.auth.models import User
from django.conf import settings
from arches_he_data_transformation.etl_modules.bulk_html_from_csv_exporter import (
    BulkHTMLFromCSVExporter,
)
from .base_test import BaseBulkHtmlTestCase
from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile

# These tests can be run from the command line via:
#     python manage.py test tests.arches_he_data_transformation.test_bulk_html_report_generation --settings="tests.test_settings"
# or if using Docker:
#     python manage.py test tests.arches_he_data_transformation.test_bulk_html_report_generation --settings="tests.test_settings_for_docker"


class TestBulkHTMLReportGeneration(BaseBulkHtmlTestCase):

    def create_csv_file_request(self, file_path, file_name):
        rf = RequestFactory()
        with open(file_path, "rb") as f:
            upload = SimpleUploadedFile(file_name, f.read(), content_type="text/csv")

        post_data = {
            "module": "96953941-79b3-440d-9c3c-a4d7a6110a37",
            "load_id": "21186e24-e407-4726-adc3-6c5e259c06cd",
        }
        # Let RequestFactory set a valid multipart boundary automatically
        request = rf.post("/etl-manager", data={**post_data, "file": upload})
        request.user = self.admin
        request.load_id = "21186e24-e407-4726-adc3-6c5e259c06cd"
        return request

    # Has the ETL Module been registered?
    def test_01_etl_module_exists(self):
        etl = models.ETLModule.objects.all()
        self.assertTrue(etl.filter(name="Bulk HTML From CSV Exporter").exists())

    # Does the read function return the expected resourceinstanceids for the test data?
    def test_02_etl_module_resourceids_read(self):

        csv_file_path = os.path.join("tests", "test_data", "test_data_csv_1.csv")

        request = self.create_csv_file_request(
            file_path=csv_file_path, file_name="test_data_csv_1.csv"
        )

        exporter = BulkHTMLFromCSVExporter()
        result = exporter.read(request=request)

        result_resourceids = len(result["data"]["resourceids"])

        self.assertTrue(result_resourceids == 2)

    def test_03_etl_module_invalid_file_header(self):
        # Use invalid CSV with wrong header ('resources' instead of 'resourceinstanceid')
        csv_file_path = os.path.join("tests", "test_data", "test_data_csv_2.csv")

        request = self.create_csv_file_request(
            file_path=csv_file_path, file_name="test_data_csv_2.csv"
        )

        exporter = BulkHTMLFromCSVExporter()
        # Expect ValueError due to missing 'resourceinstanceid' header
        with self.assertRaises(ValueError):
            exporter.read(request=request)

    def test_04_etl_module_return_resourceids(self):

        csv_file_path = os.path.join("tests", "test_data", "test_data_csv_1.csv")

        request = self.create_csv_file_request(
            file_path=csv_file_path, file_name="test_data_csv_1.csv"
        )

        exporter = BulkHTMLFromCSVExporter()

        read_result = exporter.read(request=request)
        self.assertTrue(read_result["success"])
        self.assertIn("data", read_result)
        self.assertIn("resourceids", read_result["data"])

        resourceids = read_result["data"]["resourceids"]
        graphs_and_resources = exporter.return_graphs_and_resources(resourceids)

        self.assertIsInstance(graphs_and_resources, dict)
        # Ensure the test graph id is present and contains the expected resource ids
        self.assertIn(self.test_model_graph_id, graphs_and_resources)
        self.assertEqual(
            set(graphs_and_resources[self.test_model_graph_id]), set(resourceids)
        )

    def test_05_etl_module_return_html_zip_file(self):

        csv_file_path = os.path.join("tests", "test_data", "test_data_csv_1.csv")

        request = self.create_csv_file_request(
            file_path=csv_file_path, file_name="test_data_csv_1.csv"
        )

        exporter = BulkHTMLFromCSVExporter()

        # Determine zip output directory and snapshot pre-existing files
        zip_dir = os.path.join(settings.MEDIA_ROOT, "export_deliverables")
        try:
            os.makedirs(zip_dir, exist_ok=True)
        except Exception:
            pass
        before_files = set(os.listdir(zip_dir)) if os.path.isdir(zip_dir) else set()

        # Run export task
        resourceids = exporter.read(request=request)["data"]["resourceids"]
        result = exporter.run_export_task(self.admin.id, request.load_id, resourceids)
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success"))

        # Identify newly created zip file
        after_files = set(os.listdir(zip_dir))
        new_files = list(after_files - before_files)
        self.assertEqual(len(new_files), 1, "Expected exactly one new zip file created")
        new_zip_name = new_files[0]
        self.assertTrue(new_zip_name.endswith(".zip"))

        # Open zip and assert it contains exactly one HTML file (.htm or .html)
        new_zip_path = os.path.join(zip_dir, new_zip_name)
        with zipfile.ZipFile(new_zip_path, "r") as zf:
            names = zf.namelist()
            html_files = [n for n in names if n.lower().endswith((".htm", ".html"))]
            self.assertEqual(
                len(html_files),
                1,
                "Zip should contain exactly one .htm or .html file",
            )

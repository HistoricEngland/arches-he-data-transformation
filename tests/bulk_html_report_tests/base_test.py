import os
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.conf import settings
from arches.app.models import models
from arches.app.models.graph import Graph


class BaseBulkHtmlTestCase(TestCase):
    """
    Base test case that performs heavy setup once per class using setUpTestData.
    This avoids rebuilding ontology, graphs, and business data before every test.
    """

    test_model_graph_id = "2507c336-f028-4648-a154-0dca20a9bc5e"

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.get(username="admin")

        # Snapshot current export output directory to identify new files later
        cls.export_dir = os.path.join(settings.MEDIA_ROOT, "export_deliverables")
        try:
            os.makedirs(cls.export_dir, exist_ok=True)
        except Exception:
            pass
        cls._initial_zip_files = set(os.listdir(cls.export_dir)) if os.path.isdir(cls.export_dir) else set()

        # Import ontology once
        ontology_source = os.path.join(
            "tests", "fixtures", "pkg", "ontologies", "cidoc_crm"
        )
        call_command("load_ontology", "-s", ontology_source)

        # Import and publish test graph once
        graph_source = os.path.join(
            "tests", "fixtures", "pkg", "graphs", "resource_models", "Test_Model.json"
        )
        call_command("packages", "-o", "import_graphs", "-s", graph_source)

        graph = Graph.objects.get(graphid=cls.test_model_graph_id)
        graph.publish(user=cls.admin)

        # Import business data once
        data_source = os.path.join(
            "tests",
            "fixtures",
            "pkg",
            "business_data",
            "Test_Model_Data.json",
        )
        call_command("packages", "-o", "import_business_data", "-s", data_source, "-ow", "overwrite")

    @classmethod
    def tearDownClass(cls):
        """
        Remove any test-created files and data:
        - Delete newly created zip files under MEDIA_ROOT/export_deliverables
        - Delete resource instances created for the test graph
        - Delete the test graph itself
        """
        try:
            if os.path.isdir(cls.export_dir):
                current_files = set(os.listdir(cls.export_dir))
                new_files = current_files - getattr(cls, "_initial_zip_files", set())
                for fname in new_files:
                    fpath = os.path.join(cls.export_dir, fname)
                    # Only remove regular files
                    if os.path.isfile(fpath):
                        try:
                            os.remove(fpath)
                        except Exception:
                            pass
        except Exception:
            pass

        try:
            models.ResourceInstance.objects.filter(graph_id=cls.test_model_graph_id).delete()
        except Exception:
            pass

        try:
            Graph.objects.filter(graphid=cls.test_model_graph_id).delete()
        except Exception:
            pass

        super().tearDownClass()



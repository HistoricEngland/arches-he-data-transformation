import os
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test.utils import captured_stdout
from arches.app.models import models
from arches.app.models.graph import Graph


class BaseAutopopulateFunctionTestCase(TestCase):
    """
    Base test case for AutopopulateNodeFromCardNodes function tests.

    Loads the Autopopulate_Test_Model graph and ontology once per class using
    setUpTestData, rather than before every individual test, to keep the suite
    fast. Individual tests create their own Resource and Tile instances in setUp;
    those are cleaned up automatically by Django's per-test SAVEPOINT rollback.
    """

    test_model_graph_id = "b1c2d3e4-f000-0000-0000-000000000001"

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.get(username="admin")

        # Function registration is handled by migration
        # 91002_autopopulate_function_registration, which runs as part of
        # test database creation.  No manual seeding is needed here.
        #
        # ── Adding tests for a new function ──────────────────────────────────
        # If the new function shares this graph, add a new test_<feature>.py
        # to this sub-package inheriting from this base class, and create a
        # migration (next in sequence after 91002) that calls
        # Function.objects.update_or_create() for the new function —
        # following the pattern in 91002_autopopulate_function_registration.py.
        # If the new function needs a different graph/fixture, create a new
        # sub-package (e.g. function_tests_<feature>/) with its own base_test.py.
        # ─────────────────────────────────────────────────────────────────────

        # Load CIDOC-CRM ontology (required by the test graph).
        ontology_source = os.path.join(
            "tests", "fixtures", "pkg", "ontologies", "cidoc_crm"
        )
        with captured_stdout():
            call_command("load_ontology", "-s", ontology_source)

        # Import the test graph and publish it.
        graph_source = os.path.join(
            "tests",
            "fixtures",
            "pkg",
            "graphs",
            "resource_models",
            "Autopopulate_Test_Model.json",
        )
        with captured_stdout():
            call_command("packages", "-o", "import_graphs", "-s", graph_source)

        graph = Graph.objects.get(graphid=cls.test_model_graph_id)
        graph.publish(user=cls.admin)

    @classmethod
    def tearDownClass(cls):
        """
        Remove the test graph and any resource instances that were not already
        rolled back by Django's transaction machinery (e.g. resources created
        outside of a per-test SAVEPOINT).
        """
        try:
            models.ResourceInstance.objects.filter(
                graph_id=cls.test_model_graph_id
            ).delete()
        except Exception:
            pass

        try:
            Graph.objects.filter(graphid=cls.test_model_graph_id).delete()
        except Exception:
            pass

        super().tearDownClass()

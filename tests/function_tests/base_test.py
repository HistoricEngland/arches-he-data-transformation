import os
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test.utils import captured_stdout
from arches.app.models import models
from arches.app.models.graph import Graph
from arches_he_data_transformation.functions.autopopulate_node_from_card_nodes_function import (
    details as AUTOPOPULATE_FUNCTION_DETAILS,
)


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

        # Register the function in the test database.
        # In a live environment this is done by `packages -o install`; the test
        # database starts empty so we create the record directly from the
        # function module's own `details` dict.
        #
        # ── Adding tests for a new function ──────────────────────────────────
        # If the new function shares this graph, add another get_or_create block
        # here (importing that function's `details`) and add a new
        # test_<feature>.py to this sub-package inheriting from this base class.
        # If the new function needs a different graph/fixture, create a new
        # sub-package (e.g. function_tests_<feature>/) with its own base_test.py
        # that registers only the relevant function(s).
        # ─────────────────────────────────────────────────────────────────────
        models.Function.objects.get_or_create(
            functionid=AUTOPOPULATE_FUNCTION_DETAILS["functionid"],
            defaults={
                "name": AUTOPOPULATE_FUNCTION_DETAILS["name"],
                "functiontype": AUTOPOPULATE_FUNCTION_DETAILS["type"],
                "description": AUTOPOPULATE_FUNCTION_DETAILS["description"],
                "defaultconfig": AUTOPOPULATE_FUNCTION_DETAILS["defaultconfig"],
                "modulename": "autopopulate_node_from_card_nodes_function",
                "classname": AUTOPOPULATE_FUNCTION_DETAILS["classname"],
                "component": AUTOPOPULATE_FUNCTION_DETAILS["component"],
            },
        )

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

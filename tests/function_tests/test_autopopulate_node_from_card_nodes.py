# These tests can be run from the command line via:
#
#   python manage.py test tests.function_tests.test_autopopulate_node_from_card_nodes \
#       --settings="tests.test_settings"
#
# or, when using Docker / CI:
#
#   python manage.py test tests.function_tests.test_autopopulate_node_from_card_nodes \
#       --settings="tests.test_settings_for_docker"

import uuid

from django.contrib.auth.models import User
from django.test.client import RequestFactory
from django.urls import reverse

from arches.app.models import models as arches_models
from arches.app.models.graph import Graph
from arches.app.models.resource import Resource
from arches.app.models.tile import Tile

from arches_he_data_transformation.functions.autopopulate_node_from_card_nodes_function import (
    AutopopulateNodeFromCardNodes,
)

from .base_test import BaseAutopopulateFunctionTestCase

# ---------------------------------------------------------------------------
# UUIDs – must match the nodes declared in Autopopulate_Test_Model.json
# ---------------------------------------------------------------------------

AUTOPOPULATE_TEST_GRAPH_ID = "b1c2d3e4-f000-0000-0000-000000000001"
PERSON_DETAILS_NODEGROUP_ID = "b1c2d3e4-f000-0000-0000-000000000003"
FIRST_NAME_NODE_ID = "b1c2d3e4-f000-0000-0000-000000000004"
LAST_NAME_NODE_ID = "b1c2d3e4-f000-0000-0000-000000000005"
FULL_NAME_NODE_ID = "b1c2d3e4-f000-0000-0000-000000000006"

# functionid declared in the details dict of the function module.
FUNCTION_ID = "184332d6-687d-4bcb-ae41-9aeb467fbdad"

# ---------------------------------------------------------------------------
# Function configuration constants
# ---------------------------------------------------------------------------

# Config used when the target node should be overwritten on every save.
FUNCTION_CONFIG_OVERWRITE_TRUE = {
    "autopopulate_configs": [
        {
            "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
            "target_node": FULL_NAME_NODE_ID,
            "string_template": "<First Name> <Last Name>",
            "overwrite": True,
        }
    ],
    "triggering_nodegroups": [PERSON_DETAILS_NODEGROUP_ID],
}

# Config used when the target node must NOT be overwritten if it already has a value.
FUNCTION_CONFIG_OVERWRITE_FALSE = {
    "autopopulate_configs": [
        {
            "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
            "target_node": FULL_NAME_NODE_ID,
            "string_template": "<First Name> <Last Name>",
            "overwrite": False,
        }
    ],
    "triggering_nodegroups": [PERSON_DETAILS_NODEGROUP_ID],
}


class AutopopulateNodeFromCardNodesTests(BaseAutopopulateFunctionTestCase):
    """
    Integration tests for AutopopulateNodeFromCardNodes.

    NOTE – deviation from the standard function-test pattern in HeDevUnitTestGuide.md:
    The guide recommends registering the function in ``functions_x_graphs`` inside
    the fixture and testing via ``Tile.save(request=...)``, which lets Arches dispatch
    the function automatically.  That pattern cannot be used safely here because
    ``autopopulate_nodes()`` modifies the *same* tile it is processing and calls
    ``tile.save()`` on it before returning.  If the function were registered for that
    nodegroup, the internal ``tile.save()`` would re-trigger ``_getFunctionClassInstances()``,
    find the function again, and produce infinite recursion (particularly with
    ``overwrite=True``).  The GeoJSON→BNG example in the guide avoids this by writing
    to a *different* nodegroup.

    To stay safe, these tests call ``func.save()`` directly on an in-memory ``Tile``
    and assert on ``tile.data`` in memory.  The fixture therefore leaves
    ``functions_x_graphs`` empty.

    Each test creates a fresh Resource in setUp; Django's per-test SAVEPOINT
    rolls it back automatically when the test ends.
    """

    def setUp(self):
        self.graph = Graph.objects.get(pk=AUTOPOPULATE_TEST_GRAPH_ID)
        self.resource = Resource(
            resourceinstanceid=uuid.uuid4(), graph=self.graph
        )
        self.resource.save()

        # A lightweight POST-like request carrying an admin user, as required
        # by AutopopulateNodeFromCardNodes.save() (request=None causes early return).
        self.request = RequestFactory().get(reverse("tile"))
        self.request.user = User.objects.get(username="admin")
        self.request.method = "POST"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _make_tile(self, first_name=None, last_name=None, full_name=None):
        """
        Build an in-memory Tile for the Person Details nodegroup.

        String values follow the Arches string-datatype storage format:
        ``{language_code: {"value": <str>, "direction": "ltr"}}``.
        Pass ``None`` to leave a node without a value.
        """

        def _str_val(text):
            return {"en": {"value": text, "direction": "ltr"}} if text else None

        return Tile(
            nodegroup_id=PERSON_DETAILS_NODEGROUP_ID,
            resourceinstance_id=self.resource.resourceinstanceid,
            data={
                FIRST_NAME_NODE_ID: _str_val(first_name),
                LAST_NAME_NODE_ID: _str_val(last_name),
                FULL_NAME_NODE_ID: _str_val(full_name),
            },
            sortorder=0,
        )

    def _full_name_text_values(self, tile):
        """
        Extract the plain-text values from the Full Name node's localised dict.

        Returns a list of strings (one per language key that is present).
        """
        raw = tile.data.get(FULL_NAME_NODE_ID)
        if not isinstance(raw, dict):
            return []
        return [v.get("value", "") for v in raw.values() if isinstance(v, dict)]

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_function_is_registered(self):
        """
        The AutopopulateNodeFromCardNodes function must be registered in the
        Arches Function model with the expected functionid.
        """
        self.assertTrue(
            arches_models.Function.objects.filter(functionid=FUNCTION_ID).exists()
        )

    def test_autopopulate_populates_target_from_source_nodes(self):
        """
        When both source nodes carry values, the target (Full Name) must be
        populated by substituting the node names in the string template.
        """
        tile = self._make_tile(first_name="John", last_name="Smith")
        func = AutopopulateNodeFromCardNodes(config=FUNCTION_CONFIG_OVERWRITE_TRUE)

        func.save(tile=tile, request=self.request)

        self.assertIsNotNone(tile.data[FULL_NAME_NODE_ID])
        self.assertIn("John Smith", self._full_name_text_values(tile))

    def test_autopopulate_does_not_overwrite_when_disabled(self):
        """
        With ``overwrite=False``, an existing non-empty target value must be
        preserved and must not be replaced by a new template expansion.
        """
        tile = self._make_tile(
            first_name="Jane", last_name="Doe", full_name="Existing Name"
        )
        func = AutopopulateNodeFromCardNodes(config=FUNCTION_CONFIG_OVERWRITE_FALSE)

        func.save(tile=tile, request=self.request)

        values = self._full_name_text_values(tile)
        self.assertIn("Existing Name", values)
        self.assertNotIn("Jane Doe", values)

    def test_autopopulate_overwrites_existing_value_when_enabled(self):
        """
        With ``overwrite=True``, an existing target value must be replaced by
        the newly expanded template string.
        """
        tile = self._make_tile(
            first_name="Jane", last_name="Doe", full_name="Old Name"
        )
        func = AutopopulateNodeFromCardNodes(config=FUNCTION_CONFIG_OVERWRITE_TRUE)

        func.save(tile=tile, request=self.request)

        values = self._full_name_text_values(tile)
        self.assertIn("Jane Doe", values)
        self.assertNotIn("Old Name", values)

    def test_autopopulate_skips_when_request_is_none(self):
        """
        When ``request=None`` the function must return immediately without
        modifying the tile (guards against triggering during bulk imports).
        """
        tile = self._make_tile(first_name="John", last_name="Smith")
        func = AutopopulateNodeFromCardNodes(config=FUNCTION_CONFIG_OVERWRITE_TRUE)

        func.save(tile=tile, request=None)

        # Tile data must remain exactly as constructed — Full Name still None.
        self.assertIsNone(tile.data[FULL_NAME_NODE_ID])

    def test_autopopulate_handles_empty_source_node_value(self):
        """
        When a source node is present in the tile but carries no value, its
        placeholder in the template must be replaced with an empty string
        rather than raising an exception.
        """
        tile = self._make_tile(first_name="John")  # last_name left as None
        func = AutopopulateNodeFromCardNodes(config=FUNCTION_CONFIG_OVERWRITE_TRUE)

        func.save(tile=tile, request=self.request)

        self.assertIsNotNone(tile.data[FULL_NAME_NODE_ID])
        values = self._full_name_text_values(tile)
        # "John " (first name with trailing space) should contain "John".
        self.assertTrue(
            any("John" in v for v in values),
            msg=f"Expected 'John' in full-name values; got {values}",
        )

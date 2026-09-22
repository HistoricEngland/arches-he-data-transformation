# Run this file:
#
#   python manage.py test tests.function_tests.test_autopopulate_node_from_card_nodes \
#       --settings="tests.test_settings"
#
# Run the full function_tests sub-package:
#
#   python manage.py test tests.function_tests --settings="tests.test_settings"
#
# Docker / CI equivalents – replace test_settings with test_settings_for_docker:
#
#   python manage.py test tests.function_tests.test_autopopulate_node_from_card_nodes \
#       --settings="tests.test_settings_for_docker"
#
#   python manage.py test tests.function_tests --settings="tests.test_settings_for_docker"

import types
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

# Second nodegroup – Location Details (also in Autopopulate_Test_Model.json)
LOCATION_DETAILS_NODEGROUP_ID = "b1c2d3e4-f000-0000-0000-000000000013"
CITY_NODE_ID = "b1c2d3e4-f000-0000-0000-000000000014"
COUNTRY_NODE_ID = "b1c2d3e4-f000-0000-0000-000000000015"
LOCATION_SUMMARY_NODE_ID = "b1c2d3e4-f000-0000-0000-000000000016"

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

# Config with two rules: one for each nodegroup, used to test that only the
# matching rule fires for a given tile's nodegroup.
FUNCTION_CONFIG_MULTI_RULE = {
    "autopopulate_configs": [
        {
            "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
            "target_node": FULL_NAME_NODE_ID,
            "string_template": "<First Name> <Last Name>",
            "overwrite": True,
        },
        {
            "nodegroup": LOCATION_DETAILS_NODEGROUP_ID,
            "target_node": LOCATION_SUMMARY_NODE_ID,
            "string_template": "<City>, <Country>",
            "overwrite": True,
        },
    ],
    "triggering_nodegroups": [
        PERSON_DETAILS_NODEGROUP_ID,
        LOCATION_DETAILS_NODEGROUP_ID,
    ],
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

    Integration tests following standard Arches function-test conventions, with
    one documented deviation:

    **Standard pattern**:
        Register the function in ``functions_x_graphs`` inside the fixture, then
        call ``tile.save(request=...)`` so Arches dispatches the function
        automatically.  Query the database to verify side effects.

    **Why we deviate**:
        ``autopopulate_nodes()`` modifies the *same* tile it receives and calls
        ``tile.save()`` on it before returning.  If the function were registered
        for the same nodegroup, that internal ``tile.save()`` would re-trigger
        ``_getFunctionClassInstances()``, find the function again, and recurse
        infinitely – particularly with ``overwrite=True``.  The GeoJSON→BNG
        example in the guide avoids this because it writes to a *different*
        nodegroup.

    **What we do instead**:
        Call ``func.save(tile=tile, request=self.request)`` directly on an
        in-memory ``Tile`` and assert on ``tile.data``.  The fixture therefore
        leaves ``functions_x_graphs`` empty.

    Each test creates a fresh Resource in ``setUp``; Django's per-test SAVEPOINT
    rolls it back automatically when the test ends.
    """

    def setUp(self):
        self.graph = Graph.objects.get(pk=AUTOPOPULATE_TEST_GRAPH_ID)
        self.resource = Resource(resourceinstanceid=uuid.uuid4(), graph=self.graph)
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

    def _make_location_tile(self, city=None, country=None, location_summary=None):
        """
        Build an in-memory Tile for the Location Details nodegroup.

        String values follow the Arches string-datatype storage format.
        Pass ``None`` to leave a node without a value.
        """

        def _str_val(text):
            return {"en": {"value": text, "direction": "ltr"}} if text else None

        return Tile(
            nodegroup_id=LOCATION_DETAILS_NODEGROUP_ID,
            resourceinstance_id=self.resource.resourceinstanceid,
            data={
                CITY_NODE_ID: _str_val(city),
                COUNTRY_NODE_ID: _str_val(country),
                LOCATION_SUMMARY_NODE_ID: _str_val(location_summary),
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

    def _location_summary_text_values(self, tile):
        """
        Extract the plain-text values from the Location Summary node's localised dict.

        Returns a list of strings (one per language key that is present).
        """
        raw = tile.data.get(LOCATION_SUMMARY_NODE_ID)
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
        tile = self._make_tile(first_name="Jane", last_name="Doe", full_name="Old Name")
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

    # ------------------------------------------------------------------
    # Multi-rule config tests
    # ------------------------------------------------------------------

    def test_multi_rule_config_fires_person_rule_for_person_tile(self):
        """
        With a two-rule config, saving a Person Details tile must populate
        Full Name and must leave Location Summary untouched.
        """
        tile = self._make_tile(first_name="Alice", last_name="Jones")
        func = AutopopulateNodeFromCardNodes(config=FUNCTION_CONFIG_MULTI_RULE)

        func.save(tile=tile, request=self.request)

        self.assertIn("Alice Jones", self._full_name_text_values(tile))
        # Location Summary node is not present on a Person Details tile.
        self.assertNotIn(LOCATION_SUMMARY_NODE_ID, tile.data)

    def test_multi_rule_config_fires_location_rule_for_location_tile(self):
        """
        With a two-rule config, saving a Location Details tile must populate
        Location Summary and must leave Full Name untouched.
        """
        tile = self._make_location_tile(city="London", country="England")
        func = AutopopulateNodeFromCardNodes(config=FUNCTION_CONFIG_MULTI_RULE)

        func.save(tile=tile, request=self.request)

        self.assertIn("London, England", self._location_summary_text_values(tile))
        # Full Name node is not present on a Location Details tile.
        self.assertNotIn(FULL_NAME_NODE_ID, tile.data)

    def test_multi_rule_config_rules_do_not_interfere_with_each_other(self):
        """
        With a two-rule config, applying the function to both a Person Details
        tile and a Location Details tile must populate each target node
        independently with the correct value from its own rule.
        """
        person_tile = self._make_tile(first_name="Bob", last_name="Smith")
        location_tile = self._make_location_tile(city="York", country="England")
        func = AutopopulateNodeFromCardNodes(config=FUNCTION_CONFIG_MULTI_RULE)

        func.save(tile=person_tile, request=self.request)
        func.save(tile=location_tile, request=self.request)

        self.assertIn("Bob Smith", self._full_name_text_values(person_tile))
        self.assertIn(
            "York, England", self._location_summary_text_values(location_tile)
        )


class AfterFunctionSaveValidationTests(BaseAutopopulateFunctionTestCase):
    """
    Unit tests for AutopopulateNodeFromCardNodes.after_function_save.

    after_function_save reads its configuration from tile.config (not from
    self.config), so these tests use a lightweight SimpleNamespace as the tile
    object rather than a full database-backed Tile.  No resource or request
    fixture is required.
    """

    # ------------------------------------------------------------------
    # Private helper
    # ------------------------------------------------------------------

    def _tile_with_configs(self, autopopulate_configs):
        """Return a minimal tile-like object with the given autopopulate_configs."""
        return types.SimpleNamespace(
            config={"autopopulate_configs": autopopulate_configs}
        )

    def _make_func(self):
        return AutopopulateNodeFromCardNodes(config={})

    # ------------------------------------------------------------------
    # Valid configurations
    # ------------------------------------------------------------------

    def test_empty_configs_list_passes(self):
        """An empty autopopulate_configs list must not raise."""
        tile = self._tile_with_configs([])
        self._make_func().after_function_save(tile, request=None)

    def test_single_complete_config_passes(self):
        """A complete, valid single-entry config must not raise."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": FULL_NAME_NODE_ID,
                    "string_template": "<First Name> <Last Name>",
                }
            ]
        )
        self._make_func().after_function_save(tile, request=None)

    def test_two_distinct_nodegroups_passes(self):
        """Two entries with distinct nodegroups must not raise."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": FULL_NAME_NODE_ID,
                    "string_template": "<First Name> <Last Name>",
                },
                {
                    "nodegroup": LOCATION_DETAILS_NODEGROUP_ID,
                    "target_node": LOCATION_SUMMARY_NODE_ID,
                    "string_template": "<City>, <Country>",
                },
            ]
        )
        self._make_func().after_function_save(tile, request=None)

    def test_non_dict_tile_config_treated_as_empty(self):
        """When tile.config is not a dict it is treated as empty – no raise."""
        tile = types.SimpleNamespace(config="not a dict")
        self._make_func().after_function_save(tile, request=None)

    def test_none_autopopulate_configs_treated_as_empty(self):
        """When autopopulate_configs is None it is treated as empty – no raise."""
        tile = types.SimpleNamespace(config={"autopopulate_configs": None})
        self._make_func().after_function_save(tile, request=None)

    # ------------------------------------------------------------------
    # Invalid configurations – structural errors
    # ------------------------------------------------------------------

    def test_non_list_autopopulate_configs_raises(self):
        """autopopulate_configs that is not a list must raise ValueError."""
        tile = types.SimpleNamespace(config={"autopopulate_configs": "not a list"})
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    def test_non_dict_entry_raises(self):
        """An entry in autopopulate_configs that is not a dict must raise ValueError."""
        tile = self._tile_with_configs(["not a dict"])
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    # ------------------------------------------------------------------
    # Invalid configurations – missing required fields
    # ------------------------------------------------------------------

    def test_missing_nodegroup_raises(self):
        """An entry without a nodegroup key must raise ValueError."""
        tile = self._tile_with_configs(
            [{"target_node": FULL_NAME_NODE_ID, "string_template": "<First Name>"}]
        )
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    def test_empty_nodegroup_raises(self):
        """An entry with an empty-string nodegroup must raise ValueError."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": "",
                    "target_node": FULL_NAME_NODE_ID,
                    "string_template": "<First Name>",
                }
            ]
        )
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    def test_missing_target_node_raises(self):
        """An entry without a target_node key must raise ValueError."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "string_template": "<First Name>",
                }
            ]
        )
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    def test_empty_target_node_raises(self):
        """An entry with an empty-string target_node must raise ValueError."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": "",
                    "string_template": "<First Name>",
                }
            ]
        )
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    def test_missing_string_template_raises(self):
        """An entry without a string_template key must raise ValueError."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": FULL_NAME_NODE_ID,
                }
            ]
        )
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    def test_whitespace_only_string_template_raises(self):
        """A string_template containing only whitespace must raise ValueError."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": FULL_NAME_NODE_ID,
                    "string_template": "   ",
                }
            ]
        )
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    def test_empty_string_template_raises(self):
        """A string_template that is an empty string must raise ValueError."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": FULL_NAME_NODE_ID,
                    "string_template": "",
                }
            ]
        )
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    # ------------------------------------------------------------------
    # Duplicate nodegroup rule
    # ------------------------------------------------------------------

    def test_duplicate_nodegroup_raises(self):
        """Two entries sharing the same nodegroup must raise ValueError."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": FULL_NAME_NODE_ID,
                    "string_template": "<First Name> <Last Name>",
                },
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": LAST_NAME_NODE_ID,
                    "string_template": "<First Name>",
                },
            ]
        )
        with self.assertRaises(ValueError):
            self._make_func().after_function_save(tile, request=None)

    def test_duplicate_nodegroup_error_message(self):
        """The ValueError for a duplicate nodegroup must name the constraint."""
        tile = self._tile_with_configs(
            [
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": FULL_NAME_NODE_ID,
                    "string_template": "<First Name>",
                },
                {
                    "nodegroup": PERSON_DETAILS_NODEGROUP_ID,
                    "target_node": LAST_NAME_NODE_ID,
                    "string_template": "<First Name>",
                },
            ]
        )
        with self.assertRaises(ValueError) as ctx:
            self._make_func().after_function_save(tile, request=None)
        self.assertIn("card", str(ctx.exception).lower())

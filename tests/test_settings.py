"""
ARCHES - a program developed to inventory and manage immovable cultural heritage.
Copyright (C) 2013 J. Paul Getty Trust and World Monuments Fund

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import os

from arches_he_data_transformation.settings import *

PACKAGE_NAME = "arches_he_data_transformation"

PROJECT_TEST_ROOT = os.path.dirname(__file__)
MEDIA_ROOT = os.path.join(PROJECT_TEST_ROOT, "fixtures", "data")

RESOURCE_GRAPH_LOCATIONS = [
    os.path.join(PROJECT_TEST_ROOT, "fixtures", "resource_graphs"),
    os.path.join(
        PROJECT_TEST_ROOT,
        "fixtures",
        "testing_prj",
        "testing_prj",
        "pkg",
        "graphs",
        "resource_models",
    ),
    os.path.join(PROJECT_TEST_ROOT, "fixtures", "jsonld_base", "models"),
]
REFERENCE_DATA_FIXTURE_LOCATION = os.path.join(
    PROJECT_TEST_ROOT, "fixtures", "testing_prj", "testing_prj", "pkg", "reference_data"
)

TEMPLATES[0]["DIRS"].append(os.path.join(PROJECT_TEST_ROOT, "templates"))

ONTOLOGY_FIXTURES = os.path.join(
    PROJECT_TEST_ROOT, "fixtures", "ontologies", "test_ontology"
)
ONTOLOGY_PATH = os.path.join(PROJECT_TEST_ROOT, "fixtures", "ontologies", "cidoc_crm")
MEDIA_ROOT = os.path.join(PROJECT_TEST_ROOT, "fixtures", "data")

BUSINESS_DATA_FILES = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

DATABASES = {
    "default": {
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_MAX_AGE": 0,
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "HOST": "localhost",
        "NAME": "arches_he_data_transformation",
        "OPTIONS": {},
        "PASSWORD": "postgis",
        "PORT": "5432",
        "POSTGIS_TEMPLATE": "template_postgis",
        "TEST": {"CHARSET": None, "COLLATION": None, "MIRROR": None, "NAME": None},
        "TIME_ZONE": None,
        "USER": "postgres",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
    "user_permission": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        "LOCATION": "user_permission_cache",
    },
}

LOGGING["loggers"]["arches"]["level"] = "ERROR"

ELASTICSEARCH_PREFIX = "test"

TEST_RUNNER = "arches.test.runner.ArchesTestRunner"
SILENCED_SYSTEM_CHECKS.append(
    "arches.W001",  # Cache backend does not support rate-limiting
)

ELASTICSEARCH_HOSTS = [
    {"scheme": "http", "host": "localhost", "port": ELASTICSEARCH_HTTP_PORT}
]

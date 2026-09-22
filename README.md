# arches-he-data-transformation

An Arches application which contains extensions relating to data transformation for Arches-based projects.  Designed for easy integration with Arches projects (Historic England context).

## Requirements

- Python 3.10+ (Check the Arches python requirements and match your Python version)
- Arches ==7.6.22

## Contents Overview

This Arches application contains extensions that allow the following:
- Bulk HTML export using an ETL Module where the input is a CSV file containing resource instance ids in a column with the header 'resourceid' to identify the resources for bulk HTML export.
- Auto populate node populates a target string node using values from other nodes in the same card, triggered on save, with configurable templates, multiple mappings, and optional overwriting of existing values.

## Installing for Development

For development purposes, you can treat this app as a standard Arches project. Either use the instructions for developing an Arches project or use the arches-containers configuration included in this repository.

- **For development (standard):**

  ```bash
  pip install -e '/path/to/arches_he_data_transformation[dev]'
  ```

  This installs the app in editable mode, allowing you to make changes and see them reflected immediately without needing to reinstall.

- **For development using included arches-container configuration:**
  
  Please ensure that you clone the arches-he-data-transformation repository into a directory that uses underscores instead of hyphens, as the arches-containers configuration expects this format. For example, clone it to `arches_he_data_transformation`.

  ```bash
  git clone https://github.com/HistoricEngland/arches-he-data-transformation.git arches_he_data_transformation
  ```

  This repository includes an `arches-containers` project configuration, so you can import, activate, and start the system as follows:

  1. Ensure Docker is installed and running.
  2. Navigate to your workspace directory (the root where your projects and containers live).
  3. Import the arches-container project configuration:

     ```bash
     act import -p arches_he_data_transformation
     ```

  4. Activate the project:

     ```bash
     act activate -p arches_he_data_transformation
     ```

  5. Start the system:

     ```bash
     act up
     ```

  6. Once setup and webpack builds are complete, open a browser and navigate to `http://localhost:8002` or use `act view` in a terminal to open the project in your default browser.

  For more details, see the [arches-containers documentation](https://github.com/HistoricEngland/arches-containers).


## Running Tests

> If using arches-containers, run these commands inside the application container.

The test suite uses `arches.test.runner.ArchesTestRunner` (which creates and tears down Elasticsearch indices automatically) and Django's `TestCase` for per-test transaction isolation. Tests are organised into named sub-packages under `tests/`, each containing a `base_test.py` with shared setup and one or more `test_<feature>.py` files.

### 1. Configure Test Settings

**Docker / CI (arches-containers)**

Copy the Docker settings template. The environment variables it requires are set automatically by arches-containers:

```bash
cp tests/test_settings_for_docker.py.template tests/test_settings_for_docker.py
```

> `tests/test_settings_for_docker.py` is in `.gitignore` and must never be committed.

**Local (non-Docker)**

`tests/test_settings.py` is already configured for a local PostgreSQL instance. Ensure your local database is running and matches the credentials in that file.

### 2. Run the Tests

Run the full test suite:

```bash
python manage.py test tests --settings="tests.test_settings_for_docker"
```

Run all tests in a sub-package (e.g. function tests only):

```bash
python manage.py test tests.function_tests --settings="tests.test_settings_for_docker"
```

Run a specific test file:

```bash
python manage.py test tests.function_tests.test_autopopulate_node_from_card_nodes \
    --settings="tests.test_settings_for_docker"
```

For local (non-Docker) runs, replace `test_settings_for_docker` with `test_settings`.

### Adding New Tests

Follow the existing sub-package structure under `tests/`: create a named sub-package (e.g. `function_tests/`), add an `__init__.py`, write a `base_test.py` inheriting from `django.test.TestCase` with `setUpTestData` for shared fixture loading, and add `test_<feature>.py` files inheriting from that base class.


## Using This App in Your Arches Project

Follow these steps to add `arches-he-data-transformation` to your Arches project:

### 1. Add to `your_project/pyproject.toml`

  Add the following to your `pyproject.toml` dependencies (in the `[project]` section):

  ```toml
arches-he-data-transformation @ git+https://github.com/HistoricEngland/arches-he-data-transformation.git@release/1.0.0
  ```

  Example:

  ```toml
  dependencies = [
      "arches==7.6.22",
      "arches-he-data-transformation @ git+https://github.com/HistoricEngland/arches-he-data-transformation.git@release/1.0.0",
  ]
  ```

### 2. Update `your_project/your_project/settings.py`

Add the following to the appropriate locations:

```python
ETL_MODULE_LOCATIONS.append("arches_he_data_transformation.etl_modules")
```

Add to `INSTALLED_APPS` and `ARCHES_APPLICATIONS`:

```python
INSTALLED_APPS = (
    ...
    "your_project",
    "arches_he_data_transformation",
)
ARCHES_APPLICATIONS = ("arches_he_data_transformation",)
```

### 3. Update `your_project/your_project/urls.py`

Include the app's URLs (add project URLs before this):

```python
urlpatterns = [
    # ... your project urls ...
    path("", include("arches_he_data_transformation.urls")),
]
```

### 4. Run Database Migrations

Run the following command to apply any database migrations required by this app:

> if using the arches-containers, run this in the application container

```bash
python manage.py migrate
```


## 5. Install and Build Front-End Dependencies

From the directory containing your `your_project/package.json`:

> if using arches-containers, run this in the application container or restart the webpack

```bash
npm install
npm run build_development
```

## 6. Start Your Arches Project

```bash
python manage.py runserver
```

## License

This project is licensed under the GNU AGPLv3. See the LICENSE file for details.

---


For more information on deploying your Arches project, see the [Arches Deployment Guide](https://arches.readthedocs.io/en/stable/deployment/).




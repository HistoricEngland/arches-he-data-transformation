# arches-he-data-transformation

An Arches application which contains extensions relating to data transformation for Arches-based projects.  Designed for easy integration with Arches projects (Historic England context).

## Requirements

- Python 3.10+ (Check the Arches python requirements and match your Python version)
- Arches ==7.6.22

## Contents Overview

This Arches application contains extensions that allow the following:
- Bulk HTML export using an ETL Module where the input is a CSV file containing resource instance ids in a column with the header 'resourceid' to identify the resources for bulk HTML export.

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

  For more details, see the [arches-containers documentation](../arches-containers/readme.md).


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




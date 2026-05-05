# arches-he-data-transformation

This is an Arches application developed and maintained by Historic England primarily for our own internal systems. The codebase is published openly in the spirit of transparency and in case it is useful to others in the Arches community.

Please read this document before raising issues or submitting pull requests.

---

## Table of Contents
- [Requirements](#requirements)
- [Application Contents Overview](#application-contents-overview)
- [Project Status & Scope](#project-status--scope)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)
- [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Using This App in Your Arches Project](#using-this-app-in-your-arches-project)
- [Code Style](#code-style)

---

## Requirements

- Python 3.10+ (Check the Arches python requirements and match your Python version)
- Arches ==7.6.22

---

## Application Contents Overview

This Arches application contains extensions that allow the following:

- Bulk HTML export using an ETL Module where the input is a CSV file containing resource instance ids in a column with the header 'resourceid' to identify the resources for bulk HTML export.

---

## Project Status & Scope

This repository is **actively developed for Historic England's internal use**. Development priorities and roadmap decisions are driven by our operational needs.

What this means for contributors:

| Contribution type | Status |
|---|---|
| Bug reports | ✅ Welcome |
| Security vulnerability reports | ✅ Please report promptly (see below) |
| Bug fix PRs | ✅ Considered — see guidance below |
| Documentation improvements | ✅ Welcome |
| Feature requests | ⚠️ Unlikely to be prioritised unless aligned with our roadmap |
| Feature PRs | ⚠️ Please discuss before investing effort — we may not accept them |

We will always acknowledge issues and PRs, but **we cannot guarantee that contributions outside of bug fixes will be merged or actioned**.

---

## Reporting Bugs

If you believe you have found a bug, please open a GitHub Issue and include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behaviour
- Your Arches version, Python version, and any other relevant environment details
- Any relevant logs or error messages

Please search existing issues before opening a new one.

---

## Security Vulnerabilities

**Please do not report security vulnerabilities via public GitHub Issues.**

Contact the Historic England development team directly at [insert contact email] so we can assess and address the issue before any public disclosure.

---

## Feature Requests

You are welcome to open an issue to suggest a feature, but please understand that:

- Features are prioritised against Historic England's internal roadmap
- We may close feature requests that are out of scope without implementing them
- We will try to explain our reasoning when we do so

If you need a feature for your own Arches deployment, forking this repository and adapting it for your needs may be the most practical route.

---

## Pull Requests

We will consider pull requests that fix confirmed bugs. Before submitting:

1. Check that an issue exists (or open one) describing the bug your PR addresses
2. Fork the repository and create a branch from `main`:
   ```bash
   git checkout -b fix/your-descriptive-branch-name
   ```
3. Keep the change focused — one bug fix per PR
4. Ensure existing tests still pass
5. Describe clearly in the PR what the bug was and how your change fixes it

**We are unlikely to accept PRs that:**
- Add new features without prior discussion and agreement
- Make significant refactoring changes
- Alter behaviour in ways that could affect Historic England's production systems

We reserve the right to decline any PR without detailed explanation, though we will aim to give feedback where possible.

---

## Installing for Development

For development purposes, you can treat this app as a standard Arches project. Either use the instructions for developing an Arches project or use the arches-containers configuration included in this repository.

- **For development (standard):**

  ```bash
  pip install -e '/path/to/arches_he_data_transformation[dev]'
  ```

  This installs the app in editable mode, allowing you to make changes and see them reflected immediately without needing to reinstall.

- **For development using included arches-container configuration:**
  
  Please ensure that you clone the arches-he-sysref-funcs repository into a directory that uses underscores instead of hyphens, as the arches-containers configuration expects this format. For example, clone it to `arches_he_data_transformation`.

  ```bash
  git clone https://github.com/HistoricEngland/arches-he-data-transformations.git arches_he_data_transformation
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

  6. Once setup and webpack builds are complete, open a browser and navigate to `http://localhost:8002` or use `act view` in a termainal to open the project in your default browser.

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


### 5. Install and Build Front-End Dependencies

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

---

## Code Style

- **Python:** Follow [PEP 8](https://pep8.org/).  Must be formatted using black formatter.
- **JavaScript / TypeScript:** Follow existing conventions in the codebase.
- **HTML / Django templates:** Keep templates clean and consistent with existing patterns.  Adhere to WCAG 2.2 AA standard where possible.

Avoid introducing new dependencies without prior discussion.

---

Thank you for your understanding. If you have questions about whether a contribution would be welcome, feel free to open a discussion issue before investing significant time.

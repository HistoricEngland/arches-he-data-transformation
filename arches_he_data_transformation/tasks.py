import importlib
import os
import logging
import shutil
from datetime import datetime
from celery import shared_task
from django.contrib.auth.models import User
from arches.app.tasks import create_user_task_record
from django.utils.translation import gettext as _
from arches.app.models import models
import arches.app.tasks as tasks


@shared_task(bind=True)
def export_bulk_html_report(self, user_id, load_id, resourceids):

    from arches_he_data_transformation.etl_modules import bulk_html_from_csv_exporter

    logger = logging.getLogger(__name__)

    status = _("Failed")

    try:
        html_exporter_object = bulk_html_from_csv_exporter.BulkHTMLFromCSVExporter(
            request=None, loadid=load_id
        )

        html_exporter_object.run_export_task(user_id, load_id, resourceids)

        # Check status from load event; set to Completed if indexed
        load_event = models.LoadEvent.objects.get(loadid=load_id)
        status = _("Completed") if load_event.status == "indexed" else _("Failed")

    except Exception as e:
        logger.error(e)
        load_event = models.LoadEvent.objects.get(loadid=load_id)
        # Ensure failure is recorded with details and marked complete
        load_event.status = "failed"
        load_event.complete = True
        try:
            raw_err = str(e)
            # Try to extract a concise message from Postgres error
            # that embeds our JSON load_details with "error_message": "..."
            try:
                import re

                m = re.search(r'"error_message"\s*:\s*"(.*?)"', raw_err, re.DOTALL)
                clean_err = m.group(1) if m else raw_err
            except Exception:
                clean_err = raw_err
            load_event.error_message = clean_err
            # Preserve existing details, but include the error message for UI
            details = load_event.load_details or {}
            if isinstance(details, str):
                try:
                    import json

                    details = json.loads(details)
                except Exception:
                    details = {"raw_load_details": details}
            # Update details dict
            details["error_message"] = clean_err
            load_event.load_details = details
        except Exception:
            # Best-effort; continue even if details assignment fails
            pass
        # Set end time to now
        try:
            load_event.load_end_time = datetime.now()
        except Exception:
            pass
        load_event.save()
        status = _("Failed")
    finally:
        # Send user notification on completion
        msg = _("Bulk HTML Export: {} ").format(status)
        user = User.objects.get(id=user_id)
        tasks.notify_completion(msg, user)


import importlib
import os
import logging
import shutil
from datetime import datetime
from celery import shared_task
from django.contrib.auth.models import User
from arches.app.tasks import create_user_task_record
from django.utils.translation import gettext as _
from arches.app.models import models
import arches.app.tasks as tasks


@shared_task(bind=True)
def export_bulk_html_report(self, user_id, load_id, resourceids):

    from arches_he_data_transformation.etl_modules import bulk_html_from_csv_exporter

    logger = logging.getLogger(__name__)

    status = _("Failed")

    try:
        html_exporter_object = bulk_html_from_csv_exporter.BulkHTMLFromCSVExporter(request=None, loadid=load_id)

        html_exporter_object.run_export_task(user_id, load_id, resourceids)

        # Check status from load event; set to Completed if indexed
        load_event = models.LoadEvent.objects.get(loadid=load_id)
        status = _("Completed") if load_event.status == "indexed" else _("Failed")

    except Exception as e:
        logger.error(e)
        load_event = models.LoadEvent.objects.get(loadid=load_id)
        # Ensure failure is recorded with details and marked complete
        load_event.status = "failed"
        load_event.complete = True
        try:
            raw_err = str(e)
            # Try to extract a concise message from Postgres error
            # that embeds our JSON load_details with "error_message": "..."
            try:
                import re

                m = re.search(r'"error_message"\s*:\s*"(.*?)"', raw_err, re.DOTALL)
                clean_err = m.group(1) if m else raw_err
            except Exception:
                clean_err = raw_err
            load_event.error_message = clean_err
            # Preserve existing details, but include the error message for UI
            details = load_event.load_details or {}
            if isinstance(details, str):
                try:
                    import json

                    details = json.loads(details)
                except Exception:
                    details = {"raw_load_details": details}
            # Update details dict
            details["error_message"] = clean_err
            load_event.load_details = details
        except Exception:
            # Best-effort; continue even if details assignment fails
            pass
        # Set end time to now
        try:
            load_event.load_end_time = datetime.now()
        except Exception:
            pass
        load_event.save()
        status = _("Failed")
    finally:
        # Send user notification on completion
        msg = _("Bulk HTML Export: {} ").format(status)
        user = User.objects.get(id=user_id)
        tasks.notify_completion(msg, user)


@shared_task(bind=True)
def run_bulk_delete_resources(self, user_id, load_id, resourceids, transaction_id=None):
    from arches_he_data_transformation.etl_modules import bulk_resource_deleter

    logger = logging.getLogger(__name__)

    status = _("Failed")

    try:
        delete_resources_object = bulk_resource_deleter.BulkResourceDeleter(request=None, loadid=load_id, transactionid=transaction_id)

        delete_resources_object.run_bulk_delete_task(user_id, load_id, resourceids, transaction_id)

        # Check status from load event
        load_event = models.LoadEvent.objects.get(loadid=load_id)
        status = _("Completed") if load_event.status in ["completed", "indexed"] else _("Failed")

    except Exception as e:
        logger.exception(e)
        load_event = models.LoadEvent.objects.get(loadid=load_id)
        load_event.status = "failed"
        load_event.complete = True
        load_event.error_message = str(e)
        try:
            details = load_event.load_details or {}
            if isinstance(details, str):
                import json

                details = json.loads(details)
            details["error_message"] = str(e)
            if transaction_id:
                details["transaction_id"] = transaction_id
            load_event.load_details = details
        except Exception:
            pass
        try:
            load_event.load_end_time = datetime.now()
        except Exception:
            pass
        load_event.save()
        status = _("Failed")
    finally:
        # Send user notification on completion
        msg = _("Bulk Delete Resources: {} ").format(status)
        user = User.objects.get(id=user_id)
        tasks.notify_completion(msg, user)

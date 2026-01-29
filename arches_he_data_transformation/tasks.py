import importlib
import os
import logging
import shutil
from celery import shared_task
from django.contrib.auth.models import User
from arches.app.tasks import create_user_task_record
from django.utils.translation import gettext as _
from arches.app.models import models
import arches.app.tasks as tasks


@shared_task(bind=True)
def export_bulk_html_report(self,user_id,load_id, resourceids):

    from arches_he_data_transformation.etl_modules import bulk_html_from_csv_exporter

    logger = logging.getLogger(__name__)

    status = _("Failed")

    try:
        html_exporter_object = bulk_html_from_csv_exporter.BulkHTMLFromCSVExporter(request=None, loadid=load_id)

        html_exporter_object.run_export_task(user_id,load_id, resourceids)

        # Check status from load event; set to Completed if indexed
        load_event = models.LoadEvent.objects.get(loadid=load_id)
        status = _("Completed") if load_event.status == "indexed" else _("Failed")

    except Exception as e:
        logger.error(e)
        load_event = models.LoadEvent.objects.get(loadid=load_id)
        load_event.status = "failed"
        load_event.save()
        status = _("Failed")
    finally:
        # Send user notification on completion
        msg = _("Bulk HTML Export: {} ").format(status)
        user = User.objects.get(id=user_id)
        tasks.notify_completion(msg, user)

    



import importlib
import os
import logging
import shutil
from celery import shared_task
from django.utils.translation import gettext as _


@shared_task

def export_bulk_html_report(self, user, resourceids):
    from arches_he_data_transformation.etl_modules import bulk_html_from_csv_exporter
    
    html_exporter_object = bulk_html_from_csv_exporter.BulkHTMLExporter()
    
    html_report_return = html_exporter_object.return_html_reports_for_resources(html_exporter_object.return_graphs_and_resources(resourceids))
    
    html_exporter_object.export_bulk_html_write_zipfile(html_report_return, None, resourceids)
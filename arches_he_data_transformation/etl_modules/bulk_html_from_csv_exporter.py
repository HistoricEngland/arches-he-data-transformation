import csv
from datetime import datetime
from datetime import timedelta
from tempfile import NamedTemporaryFile
import uuid
from arches.app.utils.data_management.resources.exporter import ResourceExporter
from arches.app.models import models
from arches.app.models.models import ResourceInstance
from arches.app.models.system_settings import settings
import arches.app.tasks as tasks
import arches_he_data_transformation.tasks as proj_tasks
from arches.app.etl_modules.decorators import load_data_async
from django.db import connection
import os
import json
import logging
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import arches.app.utils.zip as zip_utils

from django.utils.translation import gettext as _

details = {
    "etlmoduleid": "96953941-79b3-440d-9c3c-a4d7a6110a37",
    "name": "Bulk HTML From CSV Exporter",
    "description": "ETL module for exporting bulk HTML reports from Arches.",
    "etl_type": "export",
    "component": "views/components/etl_modules/bulk-html-from-csv-exporter",
    "componentname": "bulk-html-from-csv-exporter",
    "modulename": "bulk_html_from_csv_exporter.py",
    "classname": "BulkHTMLFromCSVExporter",
    "config": {"bgColor": "#f5c60a", "circleColor": "#f9dd6c"},
    "icon": "fa fa-upload",
    "slug": "bulk-html-from-csv-exporter",
    "helpsortorder": 9,
    "helptemplate": "bulk-html-from-csv-exporter-help",
}


class BulkHTMLFromCSVExporter:

    def __init__(self, request=None, loadid=None, params=None):
        self.request = request
        self.user = request.user if request else None
        self.userid = request.user.id if request else None
        self.useremail = request.user.email if request else None
        self.moduleid = request.POST.get("module") if request else None
        self.loadid = loadid
        self.params = params

    def get_resourceid_values(self, request=None):
        """
        Reads CSV file and returns all values from the 'resourceinstanceid' or 'resourceid' column
        """
        content = request.FILES.get("file")
        if content.content_type == "text/csv":
            with NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in content.chunks():
                    tmp_file.write(chunk)
                tmp_file.flush()
                tmp_file.seek(0)

                with open(tmp_file.name, "r") as f:
                    reader = csv.DictReader(f)
                    resourceid_values = []

                    if reader.fieldnames:
                        reader.fieldnames = [
                            (
                                fieldname.lstrip("\ufeff").strip()
                                if isinstance(fieldname, str)
                                else fieldname
                            )
                            for fieldname in reader.fieldnames
                        ]

                    # Determine which resource id header to use: 'resourceinstanceid' or 'resourceid'
                    csv_fieldnames = (
                        {
                            (
                                fieldname.lower()
                                if isinstance(fieldname, str)
                                else fieldname
                            ): fieldname
                            for fieldname in reader.fieldnames
                        }
                        if reader.fieldnames
                        else {}
                    )

                    resource_id_key = None
                    if "resourceinstanceid" in csv_fieldnames:
                        resource_id_key = csv_fieldnames["resourceinstanceid"]
                    elif "resourceid" in csv_fieldnames:
                        resource_id_key = csv_fieldnames["resourceid"]
                    else:
                        return {
                            "success": False,
                            "data": "Failed to read the values in your file due to incorrect headers.  Check you have a 'resourceinstanceid' or 'resourceid' column.",
                        }

                    # Extract all values from the chosen resource id column
                    for row in reader:
                        value = row.get(resource_id_key)
                        if value:  # Skip empty values
                            # Normalize: trim whitespace and common stray characters
                            normalized_value = str(value).strip()
                            try:
                                # Validate UUID format on normalized value
                                uuid.UUID(normalized_value)
                                resourceid_values.append(normalized_value)
                            except Exception:
                                return {
                                    "success": False,
                                    "data": f"CSV Column {resource_id_key} contains invalid Resource ID values.",
                                }

                    return {
                        "success": True,
                        "data": resourceid_values,
                    }
        else:
            return {
                "success": False,
                "data": "Invalid file type. Please upload a CSV file.",
            }

    def return_graphs_and_resources(self, resourceids):
        graphs_and_resources = {}
        for resourceid_value in resourceids:
            graph_value = (
                ResourceInstance.objects.filter(resourceinstanceid=resourceid_value)
                .values("graph_id")
                .first()
            )
            graph_id = str(graph_value["graph_id"])
            if graph_id in graphs_and_resources.keys():
                graphs_and_resources[graph_id].append(resourceid_value)
            else:
                graphs_and_resources[graph_id] = [resourceid_value]

        return graphs_and_resources

    def return_html_reports_for_resources(self, graph_resource_dict, resourcetotal):

        ret = []

        for k, v in graph_resource_dict.items():
            graph_id = k
            resources = v
            graph = models.GraphModel.objects.get(pk=graph_id)
            html_exporter = ResourceExporter(format="html")
            html_reports = html_exporter.export(
                graph_id=graph, resourceinstanceids=resources
            )
            ret.append(html_reports)

        return ret

    def read(self, request=None, source=None):

        # If CSV parsing returned an error dict, bubble it up

        resourceids = self.get_resourceid_values(request)

        if resourceids["success"]:
            resourceids["data"] = {
                "resourceids": resourceids["data"],
                "loadid": self.loadid,
            }

        return resourceids

    def run_export_task(self, user_id, load_id, resource_ids):

        logger = logging.getLogger(__name__)

        graphs_and_resources = self.return_graphs_and_resources(resource_ids)
        graph_name_list = []
        for k in graphs_and_resources.keys():
            graph = models.GraphModel.objects.get(pk=k)
            if graph.name["en"] not in graph_name_list:
                graph_name_list.append(graph.name["en"])

        graph_names = ", ".join(graph_name_list)

        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE load_event SET load_details = %s WHERE  loadid = (%s)""",
                (
                    json.dumps(
                        {
                            "graphs": graph_names,
                            "number_of_resources": len(resource_ids),
                        }
                    ),
                    load_id,
                ),
            )

        logger.info(
            f"Generating HTML files for resources; total resources: {len(resource_ids)}"
        )
        # Generate HTML files for the given resources; returns a list-of-lists
        html_files_nested = self.return_html_reports_for_resources(
            graphs_and_resources, len(resource_ids)
        )
        # Flatten into a single list of {'name': ..., 'outputfile': StringIO}
        html_files = [item for sublist in html_files_nested for item in sublist]

        # Create a zip stream and save directly to export_deliverables (no SearchExportHistory)
        zip_stream = zip_utils.create_zip_file(html_files, filekey="outputfile")
        zip_name = (
            f"{settings.APP_NAME}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.zip"
        )
        zip_dir = os.path.join(settings.MEDIA_ROOT, "export_deliverables")
        try:
            os.makedirs(zip_dir, exist_ok=True)
        except Exception:
            pass
        zip_path = os.path.join("export_deliverables", zip_name)
        default_storage.save(zip_path, ContentFile(zip_stream))
        logger.info(f"Saved bulk HTML export to {zip_path}")

        zip_url = settings.MEDIA_URL + zip_path

        load_details = {
            "graphs": graph_names,
            "number_of_resources": len(resource_ids),
            "zipfile": {"name": zip_name, "url": zip_url},
        }

        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE load_event SET (complete, status, load_details, load_end_time) = (%s, %s, %s, %s) WHERE  loadid = (%s)""",
                (True, "indexed", json.dumps(load_details), datetime.now(), load_id),
            )

        return {"success": True, "data": "success"}

    def export(self, request):
        self.loadid = request.POST.get("load_id")

        resourceids = self.read(request)

        if resourceids["success"] == False:
            error_msg = resourceids.get("data") or _(
                "Failed to read the values in your file. Check your file format and that you have a 'resourceinstanceid' or 'resourceid' column."
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO load_event (loadid, complete, status, error_message, load_details, etl_module_id, load_start_time, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        self.loadid,
                        True,
                        "failed",
                        error_msg,
                        json.dumps({"error_message": error_msg}),
                        self.moduleid,
                        datetime.now(),
                        self.userid,
                    ),
                )
            return {"success": False, "data": error_msg}

        else:

            with connection.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO load_event (loadid, complete, status, load_details, etl_module_id, load_start_time, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        self.loadid,
                        False,
                        "validated",
                        json.dumps(
                            {
                                "csv_filename": f"{request.FILES.get('file').name}",
                                "resourceids_count": len(
                                    resourceids.get("data", {}).get("resourceids", [])
                                ),
                            }
                        ),
                        self.moduleid,
                        datetime.now(),
                        self.userid,
                    ),
                )

            response = self.run_load_task_async(request, self.loadid)

            return response

    @load_data_async
    def run_load_task_async(self, request):

        file_reader = self.read(request)
        if file_reader["success"] == True:
            resourceids = file_reader["data"]["resourceids"]
            load_id = file_reader["data"]["loadid"]

            export_task = proj_tasks.export_bulk_html_report.apply_async(
                (self.userid, load_id, resourceids),
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE load_event SET taskid = %s WHERE loadid = %s""",
                    (export_task.task_id, load_id),
                )

        else:
            # CSV parsing failed; record failure in load_event so summary can display it
            error_msg = file_reader.get("data") or _(
                "Failed to read the values in your file.  Check your file format and that you have a 'resourceinstanceid' or 'resourceid' column."
            )
            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE load_event SET (complete, status, error_message, load_details, load_end_time) = (%s, %s, %s, %s, %s) WHERE  loadid = (%s)""",
                    (
                        True,
                        "failed",
                        error_msg,
                        json.dumps({"error_message": error_msg}),
                        datetime.now(),
                        self.loadid,
                    ),
                )

            return {"success": False, "data": error_msg}

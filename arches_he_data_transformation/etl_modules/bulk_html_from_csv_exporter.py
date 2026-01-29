import csv
from datetime import datetime
from datetime import timedelta
from tempfile import NamedTemporaryFile
from arches.app.utils.data_management.resources.exporter import ResourceExporter
from arches.app.etl_modules.base_excel_exporter import BaseExcelExporter
from arches.app.search.search_export import SearchResultsExporter
from arches.app.models import models
from arches.app.models.models import ResourceInstance
from arches.app.models.system_settings import settings
from arches.app.utils.message_contexts import return_message_context
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


class BulkHTMLFromCSVExporter(BaseExcelExporter):

    

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
        Reads CSV file and returns all values from the 'resourceid' column
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
                            (fn.lstrip("\ufeff").strip() if isinstance(fn, str) else fn)
                            for fn in reader.fieldnames]

                    # Check if 'resourceid' header exists
                    if "resourceid" not in reader.fieldnames:
                        raise ValueError("Column 'resourceid' not found in CSV headers")

                    # Extract all values from the resourceid column
                    for row in reader:
                        if row["resourceid"]:  # Skip empty values
                            resourceid_values.append(row["resourceid"])

                    return resourceid_values
        else:
            raise ValueError("File is not a CSV")

    def return_graphs_and_resources(self, resourceids):
        graphs_and_resources = {}
        for resourceid_value in resourceids:
            graph_value = ResourceInstance.objects.filter(resourceinstanceid=resourceid_value).values("graph_id").first()
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
            html_reports = html_exporter.export(graph_id=graph, resourceinstanceids=resources)
            ret.append(html_reports)

        return ret
    
    def read(self, request=None, source=None):
        resourceids = self.get_resourceid_values(request)

        return {"success": True, "data": {"resourceids": resourceids, "loadid": self.loadid}} 
    
    
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
        
        logger.info(f"Generating HTML files for resources; total resources: {len(resource_ids)}")
        # Generate HTML files for the given resources; returns a list-of-lists
        html_files_nested = self.return_html_reports_for_resources(graphs_and_resources, len(resource_ids))
        # Flatten into a single list of {'name': ..., 'outputfile': StringIO}
        html_files = [item for sublist in html_files_nested for item in sublist]

        # Create a zip stream and save directly to export_deliverables (no SearchExportHistory)
        zip_stream = zip_utils.create_zip_file(html_files, filekey="outputfile")
        zip_name = f"{settings.APP_NAME}_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.zip"
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
                "zipfile": {
                    "name": zip_name,
                    "url": zip_url
                },
            }

        with connection.cursor() as cursor:
            cursor.execute(
                """UPDATE load_event SET (complete, status, load_details, load_end_time) = (%s, %s, %s, %s) WHERE  loadid = (%s)""",
                (True, "indexed", json.dumps(load_details), datetime.now(), load_id),
            )

        return {"success": True, "data": "success"}
    
    @load_data_async
    def run_load_task_async(self, request):
        
        file_reader = self.read(request)
        if file_reader["success"]== True:
            resourceids = file_reader["data"]["resourceids"]
            load_id = file_reader["data"]["loadid"]

            
            export_task = proj_tasks.export_bulk_html_report.apply_async((self.userid, load_id, resourceids),)
            


            with connection.cursor() as cursor:
                cursor.execute(
                    """UPDATE load_event SET taskid = %s WHERE loadid = %s""",
                    (export_task.task_id, load_id),
                )  

        else:
            # CSV parsing failed; do not dispatch export task. Let UI show error.
            # Notification is handled by task flow when exports run; skip here to avoid duplicates.
            return {"success": False, "data": "CSV read failed.  Check your file format and that you have a 'resourceid' column."}


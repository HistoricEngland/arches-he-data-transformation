import csv
from datetime import datetime
from datetime import timedelta
from tempfile import NamedTemporaryFile
from arches.arches.app.utils.data_management.resources.exporter import ResourceExporter
from arches.arches.app.search.search_export import SearchResultsExporter
from arches.arches.app.models import models
from arches.arches.app.models.models import ResourceInstance
from arches.arches.app.models.system_settings import settings
from arches.arches.app.utils.message_contexts import return_message_context
import arches.arches.app.tasks as tasks
import arches_he_data_transformation.tasks as proj_tasks

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
    "helptemplate": "bulk-html-from-csv-exporter-help"
}

class BulkHTMLFromCSVExporter(ResourceExporter):

    def __init__(self, request=None, loadid=None, params=None):
        self.request = request
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
                    
                    # Check if 'resourceid' header exists
                    if 'resourceid' not in reader.fieldnames:
                        raise ValueError("Column 'resourceid' not found in CSV headers")
                    
                    # Extract all values from the resourceid column
                    for row in reader:
                        if row['resourceid']:  # Skip empty values
                            resourceid_values.append(row['resourceid'])
                    
                    return resourceid_values
        else:
            raise ValueError("File is not a CSV")

    def return_graphs_and_resources(self, resourceids):
        graphs_and_resources = {}
        for resourceid_value in resourceids:
            graph_value = ResourceInstance.objects.filter(id=resourceid_value).values("graph_id").first()
        if graph_value in graphs_and_resources.keys():
            graphs_and_resources[graph_value].append(resourceid_value)
        else:
            graphs_and_resources[graph_value] = [resourceid_value]   
            
        return graphs_and_resources
    
    def return_html_reports_for_resources(self,graph_resource_dict,resourcetotal):
               
        ret = []
        
        for k, v in graph_resource_dict.items():
            graph_id = k
            resources = v
            graph = models.GraphModel.objects.get(pk=graph_id)
            html_exporter = ResourceExporter(format="html")
            ret.append(html_exporter.export(graphid=graph,resourceinstanceids=resources))
            
        return ret
    
    def export_bulk_html_reports(self, request):
  
        resourceids = self.get_resourceid_values(request)
        export_user = request.user.id
        
        html_reports = proj_tasks.export_bulk_html_report.apply_async(export_user,resourceids)
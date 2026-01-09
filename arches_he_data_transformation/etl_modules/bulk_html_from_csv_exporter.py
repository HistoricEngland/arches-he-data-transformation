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
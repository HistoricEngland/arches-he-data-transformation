from arches.arches.app.utils.data_management.resources.exporter import ResourceExporter

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
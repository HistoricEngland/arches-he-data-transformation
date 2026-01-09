from django.db import migrations, models
from django.utils.translation import gettext as _

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("models", "11499_add_editlog_resourceinstance_idx"),
    ]

    def add_bulk_export_etl_modules(apps, schema_editor):
        ETLModule = apps.get_model("models", "ETLModule")
        ETLModule.objects.update_or_create(
            etlmoduleid="96953941-79b3-440d-9c3c-a4d7a6110a37",
            defaults={
                "name": "Bulk HTML From CSV Exporter",
                "etl_type": "export",
                "description": _("ETL module for exporting bulk HTML reports from Arches."),
                "modulename": "bulk_html_from_csv_exporter.py",
                "classname":"BulkHTMLFromCSVExporter",
                "component":"views/components/etl_modules/bulk-html-from-csv-exporter",
            }
        )

    def remove_bulk_export_etl_modules(apps, schema_editor):
        ETLModule = apps.get_model("models", "ETLModule")
        for etl in ETLModule.objects.filter(
            pk__in=[
                "96953941-79b3-440d-9c3c-a4d7a6110a37",
                ]
            ):
            etl.delete()

    operations = [
        migrations.RunPython(add_bulk_export_etl_modules, remove_bulk_export_etl_modules),
    ]
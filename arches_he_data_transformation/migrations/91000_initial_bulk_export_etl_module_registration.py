from django.db import migrations
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("models", "11499_add_editlog_resourceinstance_idx"),
        ("guardian", "0001_initial"),
    ]

    def add_bulk_export_etl_modules(apps, schema_editor):
        '''Add Bulk HTML From CSV Exporter ETL Module'''
        ETLModule = apps.get_model("models", "ETLModule")
        ETLModule.objects.update_or_create(
            etlmoduleid="96953941-79b3-440d-9c3c-a4d7a6110a37",
            defaults={
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
        )

    def remove_bulk_export_etl_modules(apps, schema_editor):
        '''Remove Bulk HTML From CSV Exporter ETL Module'''
        ETLModule = apps.get_model("models", "ETLModule")
        for etl in ETLModule.objects.filter(
            pk__in=[
                "96953941-79b3-440d-9c3c-a4d7a6110a37",
                ]
            ):
            etl.delete()

    def activate_bulk_data_manager(apps, schema_editor):
            '''Set Visibility of the Bulk Data Manager Plugin to True'''
            plugins = apps.get_model("models", "Plugin")
            for plugin in plugins.objects.all():
                if plugin.name["en"]== "Bulk Data Manager":
                    plugin.config["show"]= True
                    plugin.save()


    def add_permissions_group(apps, schema_editor, with_create_permissions=True):
        ''' Create Bulk HTML Exporter permissions group and add all named users to it'''
        db_alias = schema_editor.connection.alias
        Group = apps.get_model("auth", "Group")
        User = apps.get_model("auth", "User")
        resource_exporter_group = Group.objects.using(db_alias).create(
            name="Bulk HTML Exporter"
        )

        try:
            users = User.objects.using(db_alias)
            resource_exporter_group.user_set.add(*users)
            print("added users group")
        except Exception as e:
            print(e)

    def remove_permissions_group(apps, schema_editor, with_create_permissions=True):
        Group = apps.get_model("auth", "Group")

        try:
            Group.objects.filter(name__in=["Bulk HTML Exporter"]).delete()
            print("removed Bulk HTML Exporter group")
        except:
            pass


    def set_access_permissions(apps, schema_editor):
            ''' Set access permissions for Bulk HTML From CSV Exporter ETL Module.
            Assigns view permission to Bulk HTML Exporter group and all permissions to admin user.'''
            Group = apps.get_model("auth", "Group")
            User = apps.get_model("auth", "User")
            ETLModule = apps.get_model("models", "ETLModule")
            GroupObjectPermission = apps.get_model("guardian", "GroupObjectPermission")
            UserObjectPermission = apps.get_model("guardian", "UserObjectPermission")
            BulkHTMLEtlModule = ETLModule.objects.get(
                etlmoduleid="96953941-79b3-440d-9c3c-a4d7a6110a37"
            )
            resource_exporter_group = Group.objects.get(name="Bulk HTML Exporter")
            admin_user_id = User.objects.get(username="admin").id
            ct_id = ContentType.objects.get_for_model(BulkHTMLEtlModule).id
            all_etl_permissions = Permission.objects.filter(name__icontains="etl")

            for perm in all_etl_permissions:
                 UserObjectPermission.objects.get_or_create(
                    user_id=admin_user_id,
                    content_type_id=ct_id,
                    object_pk=str(BulkHTMLEtlModule.pk),
                    permission_id=perm.pk
                )

            GroupObjectPermission.objects.get_or_create(
                group_id=resource_exporter_group.id,
                content_type_id=ct_id,
                object_pk=str(BulkHTMLEtlModule.pk),
                permission_id=all_etl_permissions.get(codename__icontains="view").pk
            )


    operations = [
        migrations.RunPython(add_bulk_export_etl_modules, reverse_code=remove_bulk_export_etl_modules),
        migrations.RunPython(activate_bulk_data_manager),
        migrations.RunPython(add_permissions_group, reverse_code=remove_permissions_group),
        migrations.RunPython(set_access_permissions),
    ]
from django.db import migrations
from django.utils.translation import gettext as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from django.db import connection


class Migration(migrations.Migration):
    """
    As this is an initial migration for the Bulk HTML From CSV Exporter ETL Module, you need to run the following to reverse the migrations within it:
    python manage.py migrate arches_he_data_transformation zero
    For more information read the Django documentation on migrations: https://docs.djangoproject.com/en/4.2/topics/migrations/
    """

    initial = True

    dependencies = [
        ("arches_he_data_transformation",
        "91001_disable_undo_for_bulk_html_exporter",)
    ]

    def add_bulk_resource_deleter_etl_modules(apps, schema_editor):
        """Add Bulk Resource Deleter ETL Module"""
        ETLModule = apps.get_model("models", "ETLModule")
        ETLModule.objects.update_or_create(
            etlmoduleid="204e515a-a782-49e6-be98-6134e144468b",
            defaults={
                "name": "Bulk Resource Deleter",
                "description": "ETL module for deleting multiple resources from Arches.",
                "etl_type": "edit",
                "component": "views/components/etl_modules/bulk-resource-deleter",
                "componentname": "bulk-resource-deleter",
                "modulename": "bulk_resource_deleter.py",
                "classname": "BulkResourceDeleter",
                "config": {"bgColor": "#f5c60a", "circleColor": "#f9dd6c"},
                "icon": "fa fa-upload",
                "slug": "bulk-resource-deleter",
                "helpsortorder": 9,
                "helptemplate": "bulk-resource-deleter-help",
            },
        )

    def remove_bulk_resource_deleter_etl_modules(apps, schema_editor):
        """Remove Bulk Resource Deleter ETL Module"""
        ETLModule = apps.get_model("models", "ETLModule")
        for etl in ETLModule.objects.filter(
            pk__in=[
                "204e515a-a782-49e6-be98-6134e144468b",
            ]
        ):
            etl.delete()

    def add_permissions_group(apps, schema_editor, with_create_permissions=True):
        """Create Bulk Resource Deleter permissions group and add all named users to it"""
        db_alias = schema_editor.connection.alias
        Group = apps.get_model("auth", "Group")
        Group.objects.using(db_alias).create(name="Bulk Resource Deleter")

    def remove_permissions_group(apps, schema_editor, with_create_permissions=True):
        Group = apps.get_model("auth", "Group")

        try:
            Group.objects.filter(name__in=["Bulk Resource Deleter"]).delete()
            print("removed Bulk Resource Deleter group")
        except:
            pass

    def set_access_permissions(apps, schema_editor):
        """Set access permissions for Bulk Resource Deleter ETL Module.
        Assigns view permission to Bulk Resource Deleter group and all permissions to admin user.
        """
        Group = apps.get_model("auth", "Group")
        User = apps.get_model("auth", "User")
        ETLModule = apps.get_model("models", "ETLModule")
        Plugins = apps.get_model("models", "Plugin")
        GroupObjectPermission = apps.get_model("guardian", "GroupObjectPermission")
        UserObjectPermission = apps.get_model("guardian", "UserObjectPermission")
        BulkResourceDeleterEtLModule = ETLModule.objects.get(
            etlmoduleid="204e515a-a782-49e6-be98-6134e144468b"
        )
        resource_deleter_group = Group.objects.get(name="Bulk Resource Deleter")
        admin_user_id = User.objects.get(username="admin").id
        etl_ct_id = ContentType.objects.get_for_model(BulkResourceDeleterEtLModule).id
        all_etl_permissions = Permission.objects.filter(name__icontains="etl")

        for perm in all_etl_permissions:
            UserObjectPermission.objects.get_or_create(
                user_id=admin_user_id,
                content_type_id=etl_ct_id,
                object_pk=str(BulkResourceDeleterEtLModule.pk),
                permission_id=perm.pk,
            )

        GroupObjectPermission.objects.get_or_create(
            group_id=resource_deleter_group.id,
            content_type_id=etl_ct_id,
            object_pk=str(BulkResourceDeleterEtLModule.pk),
            permission_id=all_etl_permissions.get(codename__icontains="view").pk,
        )



    def migrate(apps, schema_editor, with_create_permissions=True):
        Migration.add_bulk_resource_deleter_etl_modules(apps, schema_editor)
        Migration.add_permissions_group(apps, schema_editor, with_create_permissions)
        Migration.set_access_permissions(apps, schema_editor)

    def reverse_migrate(apps, schema_editor, with_create_permissions=True):
        Migration.remove_bulk_resource_deleter_etl_modules(apps, schema_editor)
        Migration.remove_permissions_group(apps, schema_editor, with_create_permissions)

    operations = [migrations.RunPython(migrate, reverse_code=reverse_migrate)]

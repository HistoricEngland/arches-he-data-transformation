from django.db import migrations


class Migration(migrations.Migration):
    """
    Registers the AutopopulateNodeFromCardNodes function in the Arches Function
    table.  Uses update_or_create so the migration is safe to run against a
    database that already has the record (e.g. one populated by
    ``packages -o install``).

    To reverse this migration:
        python manage.py migrate arches_he_data_transformation 91001
    """

    dependencies = [
        (
            "arches_he_data_transformation",
            "91001_disable_undo_for_bulk_html_exporter",
        ),
        ("models", "11499_add_editlog_resourceinstance_idx"),
    ]

    def add_autopopulate_function(apps, schema_editor):
        Function = apps.get_model("models", "Function")
        Function.objects.update_or_create(
            functionid="184332d6-687d-4bcb-ae41-9aeb467fbdad",
            defaults={
                "name": "Automatically Fill a Field Using Other Fields",
                "functiontype": "node",
                "description": (
                    "Automatically fills a Field (Node) in a Card with the values from other "
                    "Fields within that Card"
                ),
                "defaultconfig": {
                    "autopopulate_configs": [],
                    "triggering_nodegroups": [],
                },
                "modulename": "autopopulate_node_from_card_nodes_function",
                "classname": "AutopopulateNodeFromCardNodes",
                "component": "views/components/functions/autopopulate-node-from-card-nodes-function",
            },
        )

    def remove_autopopulate_function(apps, schema_editor):
        Function = apps.get_model("models", "Function")
        Function.objects.filter(
            functionid="184332d6-687d-4bcb-ae41-9aeb467fbdad"
        ).delete()

    operations = [
        migrations.RunPython(
            add_autopopulate_function,
            reverse_code=remove_autopopulate_function,
        )
    ]

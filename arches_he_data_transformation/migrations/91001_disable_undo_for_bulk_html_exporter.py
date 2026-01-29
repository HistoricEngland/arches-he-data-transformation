from django.db import migrations


def set_reversible_false(apps, schema_editor):
    ETLModule = apps.get_model("models", "ETLModule")
    ETLModule.objects.filter(etlmoduleid="96953941-79b3-440d-9c3c-a4d7a6110a37").update(
        reversible=False
    )


def reverse_set_reversible(apps, schema_editor):
    ETLModule = apps.get_model("models", "ETLModule")
    ETLModule.objects.filter(etlmoduleid="96953941-79b3-440d-9c3c-a4d7a6110a37").update(
        reversible=True
    )


class Migration(migrations.Migration):
    dependencies = [
        (
            "arches_he_data_transformation",
            "91000_initial_bulk_export_etl_module_registration",
        ),
    ]

    operations = [
        migrations.RunPython(set_reversible_false, reverse_code=reverse_set_reversible),
    ]

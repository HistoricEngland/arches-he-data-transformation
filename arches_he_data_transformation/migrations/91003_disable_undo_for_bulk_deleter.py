from django.db import migrations


def set_reversible_false(apps, schema_editor):
    ETLModule = apps.get_model("models", "ETLModule")
    ETLModule.objects.filter(etlmoduleid="204e515a-a782-49e6-be98-6134e144468b").update(
        reversible=False
    )


def reverse_set_reversible(apps, schema_editor):
    ETLModule = apps.get_model("models", "ETLModule")
    ETLModule.objects.filter(etlmoduleid="204e515a-a782-49e6-be98-6134e144468b").update(
        reversible=True
    )


class Migration(migrations.Migration):
    dependencies = [
        (
            "arches_he_data_transformation",
            "91002_install_bulk_deleter_etl_module_registration",
        ),
    ]

    operations = [
        migrations.RunPython(set_reversible_false, reverse_code=reverse_set_reversible),
    ]

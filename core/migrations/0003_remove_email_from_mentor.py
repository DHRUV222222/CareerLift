from django.db import migrations, models


def remove_email_field(apps, schema_editor):
    """Remove the email field from existing Mentor objects."""
    Mentor = apps.get_model('core', 'Mentor')
    # This function will be called when applying the migration
    # No need to do anything as we're just removing the field
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_user_phone'),
    ]

    operations = [
        migrations.RunPython(
            remove_email_field,
            reverse_code=migrations.RunPython.noop,  # No reverse operation needed
        ),
        migrations.RemoveField(
            model_name='mentor',
            name='email',
        ),
    ]

# Generated by Django 4.1.7 on 2023-02-25 04:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('task', '0004_rename_name_taskcategory_content_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskcategory',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='contenttypes.contenttype'),
        ),
    ]

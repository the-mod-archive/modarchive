# Generated by Django 4.0.1 on 2022-06-10 03:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artists', '0008_alter_artist_key_alter_artist_legacy_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='artist',
            name='legacy_id',
            field=models.IntegerField(blank=True, help_text='User ID from the legacy Mod Archive site', null=True),
        ),
    ]

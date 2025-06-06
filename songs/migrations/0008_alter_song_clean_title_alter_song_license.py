# Generated by Django 4.0.1 on 2022-06-16 03:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0007_remove_song_hits_alter_songstats_downloads'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='clean_title',
            field=models.CharField(blank=True, db_index=True, help_text='Cleaned-up version of the title for better display and search', max_length=120, null=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='license',
            field=models.CharField(blank=True, choices=[('publicdomain', 'Public Domain'), ('by-nc', 'Non-commercial'), ('by-nc-nd', 'Non-commercial No Derivatives'), ('by-nc-sa', 'Non-commercial Share Alike'), ('by-nd', 'No Derivatives'), ('by-sa', 'Share Alike'), ('by', 'Attribution'), ('cc0', 'CC0')], max_length=16, null=True),
        ),
    ]

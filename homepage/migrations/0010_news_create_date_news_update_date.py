# Generated by Django 4.0.1 on 2022-08-02 03:27

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('homepage', '0009_alter_news_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='create_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='news',
            name='update_date',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

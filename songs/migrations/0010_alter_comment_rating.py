# Generated by Django 4.0.1 on 2022-07-01 03:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0009_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='rating',
            field=models.PositiveSmallIntegerField(choices=[(1, '1: Very poor'), (2, '2: Poor'), (3, '3: Listenable'), (4, '4: Good attempt'), (5, '5: Average'), (6, '6: Above average'), (7, '7: Enjoyable'), (8, '8: Very good'), (9, '9: Excellent'), (10, '10: Awesome')]),
        ),
    ]

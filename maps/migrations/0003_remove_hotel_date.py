# Generated by Django 3.2.5 on 2021-07-29 19:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('maps', '0002_auto_20210730_0006'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hotel',
            name='date',
        ),
    ]

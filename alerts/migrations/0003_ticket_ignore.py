# Generated by Django 2.1.4 on 2021-03-16 21:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alerts', '0002_event_resale_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='ignore',
            field=models.BooleanField(default=False),
        ),
    ]

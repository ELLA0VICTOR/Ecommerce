# Generated by Django 5.1.6 on 2025-07-04 23:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='transaction_ref',
            field=models.CharField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]

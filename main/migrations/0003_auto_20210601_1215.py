# Generated by Django 3.1.2 on 2021-06-01 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20210515_1136'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='user_image',
            field=models.ImageField(null=True, upload_to='', verbose_name='User rasmi'),
        ),
    ]
# Generated by Django 3.1.2 on 2021-06-02 14:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0004_auto_20210602_1923'),
    ]

    operations = [
        migrations.RenameField(
            model_name='answerimage',
            old_name='images',
            new_name='image',
        ),
    ]
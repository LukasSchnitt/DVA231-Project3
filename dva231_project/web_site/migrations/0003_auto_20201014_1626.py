# Generated by Django 3.1.2 on 2020-10-14 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_site', '0002_personalcocktail_user_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='personalcocktail',
            name='average',
            field=models.FloatField(default=None),
        ),
        migrations.AlterField(
            model_name='review',
            name='rating',
            field=models.IntegerField(choices=[(1, 'Bad'), (2, 'Ok'), (3, 'Good'), (4, 'Awesome'), (5, 'Perfect')], default=5),
        ),
    ]

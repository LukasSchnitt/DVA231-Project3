# Generated by Django 3.1.2 on 2020-10-26 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_site', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='personalcocktail',
            name='blacklisted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='review',
            name='is_personal_cocktail',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='review',
            name='rating',
            field=models.IntegerField(choices=[(0, 'Super Bad'), (1, 'Bad'), (2, 'Ok'), (3, 'Good'), (4, 'Awesome'), (5, 'Perfect')], default=5),
        ),
    ]

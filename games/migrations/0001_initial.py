# Generated by Django 2.1.2 on 2018-10-03 00:20

import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import games.models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fields', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('O', 'O'), ('X', 'X')], max_length=1, null=True), default=games.models.empty_fields, size=9)),
                ('first_player', models.CharField(choices=[('O', 'O'), ('X', 'X')], max_length=1, null=True)),
                ('winner', models.CharField(choices=[('O', 'O'), ('X', 'X'), ('draw', 'draw')], max_length=4, null=True)),
                ('current_turn', models.CharField(choices=[('O', 'O'), ('X', 'X')], max_length=1, null=True)),
                ('player_ids', django.contrib.postgres.fields.jsonb.JSONField(default=games.models.default_player_ids)),
            ],
        ),
    ]

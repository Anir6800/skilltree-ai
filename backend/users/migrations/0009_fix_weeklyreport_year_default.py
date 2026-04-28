"""
Schema fix: Replace hardcoded year=2026 default on WeeklyReport with a
callable that returns the current year at insert time.
"""

import datetime
from django.db import migrations, models


def current_year():
    return datetime.date.today().year


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_rename_users_adapt_user_id_idx_users_adapt_user_id_cd99c1_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weeklyreport',
            name='year',
            field=models.IntegerField(default=current_year, help_text='ISO year of the report'),
        ),
    ]

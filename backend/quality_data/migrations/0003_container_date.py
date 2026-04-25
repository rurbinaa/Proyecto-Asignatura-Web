from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("quality_data", "0002_add_kpi_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="container",
            name="date",
            field=models.DateField(blank=True, db_index=True, null=True),
        ),
    ]

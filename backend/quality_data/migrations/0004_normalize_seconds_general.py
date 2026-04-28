import django.db.models.deletion
from django.db import migrations, models


def migrate_flat_defects_to_normalized(apps, schema_editor):
    SecondsGeneral = apps.get_model("quality_data", "SecondsGeneral")
    SecondsGeneralDefectType = apps.get_model("quality_data", "SecondsGeneralDefectType")
    SecondsGeneralDefect = apps.get_model("quality_data", "SecondsGeneralDefect")

    defect_type_names = [
        "picado_aguja", "manchas_sucio", "grasa", "tono_tela", "fuera_medidas",
        "enganche", "costura_torcida_insegura", "hoyos_costura", "heat_transfer",
        "mal_corte", "trapo", "corrido", "otros",
        "desgarre_def_tela", "contamination", "linea_de_tela", "mill_flaw",
        "hoyos", "manchas_tela",
        "corrido_2", "barre", "otros_3", "degradacion", "bordados",
    ]

    for name in defect_type_names:
        SecondsGeneralDefectType.objects.get_or_create(name=name)

    defect_type_map = {
        dt.name: dt
        for dt in SecondsGeneralDefectType.objects.all()
    }

    field_to_defect_type = {
        "corrido_2": "corrido_2",
        "barre": "barre",
        "otros_3": "otros_3",
        "degradacion": "degradacion",
        "bordados": "bordados",
    }

    defects_to_create = []
    for sg in SecondsGeneral.objects.all():
        for flat_field, defect_name in field_to_defect_type.items():
            amount = getattr(sg, flat_field, 0) or 0
            if amount > 0:
                defect_type = defect_type_map.get(defect_name)
                if defect_type:
                    defects_to_create.append(
                        SecondsGeneralDefect(
                            seconds_general=sg,
                            defect_type=defect_type,
                            amount=amount,
                        )
                    )

    if defects_to_create:
        SecondsGeneralDefect.objects.bulk_create(defects_to_create, batch_size=2000, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ("quality_data", "0003_container_date"),
    ]

    operations = [
        # 1. Create defect type table
        migrations.CreateModel(
            name="SecondsGeneralDefectType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        # 2. Add metadata fields to SecondsGeneral
        migrations.AddField(
            model_name="secondsgeneral",
            name="artcode",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="secondsgeneral",
            name="color",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="secondsgeneral",
            name="customer",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="secondsgeneral",
            name="definitive",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="secondsgeneral",
            name="fixed",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="secondsgeneral",
            name="line",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="secondsgeneral",
            name="po",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="secondsgeneral",
            name="produced",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="secondsgeneral",
            name="size",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="secondsgeneral",
            name="style",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        # 3. Create defect through model (must exist before data migration)
        migrations.CreateModel(
            name="SecondsGeneralDefect",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.PositiveIntegerField(default=0)),
                ("seconds_general", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="seconds_general_defects", to="quality_data.secondsgeneral")),
                ("defect_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="seconds_general_defects", to="quality_data.secondsgeneraldefecttype")),
            ],
        ),
        # 4. Add M2M field
        migrations.AddField(
            model_name="secondsgeneral",
            name="defects",
            field=models.ManyToManyField(related_name="seconds_general_records", through="quality_data.SecondsGeneralDefect", to="quality_data.secondsgeneraldefecttype"),
        ),
        # 5. Add constraint and index
        migrations.AddConstraint(
            model_name="secondsgeneraldefect",
            constraint=models.UniqueConstraint(fields=("seconds_general", "defect_type"), name="unique_seconds_general_defect"),
        ),
        migrations.AddIndex(
            model_name="secondsgeneral",
            index=models.Index(fields=["week"], name="idx_sg_week"),
        ),
        # 6. Data migration: move flat defects to normalized
        migrations.RunPython(
            migrate_flat_defects_to_normalized,
            reverse_code=migrations.RunPython.noop,
        ),
        # 7. Remove old flat fields (after data migration)
        migrations.RemoveField(
            model_name="secondsgeneral",
            name="barre",
        ),
        migrations.RemoveField(
            model_name="secondsgeneral",
            name="bordados",
        ),
        migrations.RemoveField(
            model_name="secondsgeneral",
            name="corrido_2",
        ),
        migrations.RemoveField(
            model_name="secondsgeneral",
            name="degradacion",
        ),
        migrations.RemoveField(
            model_name="secondsgeneral",
            name="otros_3",
        ),
        migrations.RemoveField(
            model_name="secondsgeneral",
            name="total_de_tela",
        ),
    ]

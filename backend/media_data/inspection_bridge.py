"""
Inspection Bridge — Connect media_data inspections to quality_data tables.

When a tactile inspection is closed, this service:
1. Finds matching records across QualityQcFa, SecondsGeneral, SecondsA4
   by style + color + week
2. Updates accepted/rejected/defects_total based on captured defects
3. Syncs RevisionDefect records into InspectionDefect (through table)
4. Populates common fields (style, color, week, date, size) on Seconds tables

This bridges the gap between the touch capture interface (media_data)
and the QC reporting tables (quality_data).
"""

from django.db import transaction
from quality_data.models import (
    QualityQcFa,
    InspectionDefect,
    DefectType,
    SecondsGeneral,
    SecondsA4,
    SecondsGeneralDefectType,
    SecondsGeneralDefect,
)
from media_data.models import InspectionData, RevisionDefect


# Mapping from garment defect types (English, from QC FA Plant)
# to seconds defect types (Spanish, from Seconds General).
# Built from Excel header translations in sheet_configs.py REMAP dicts.
GARMENT_TO_SECONDS_DEFECT_MAP = {
    "contamination": "contamination",
    "mill_flaw": "mill_flaw",
    "tear": "desgarre_def_tela",
    "out_of_measurements": "fuera_medidas",
    "hitched": "enganche",
    "fabric_run": "corrido",
    "stain_oil_soil": "manchas_sucio",
    "dirt_marck": "manchas_sucio",
    "broken_stitch": "costura_torcida_insegura",
    "incorrect_stitch": "costura_torcida_insegura",
    "run_off_stitch": "costura_torcida_insegura",
    "neddle_holes": "picado_aguja",
    "open_seam": "hoyos_costura",
}


def bridge_inspection(inspection: InspectionData) -> dict:
    """
    Sync a closed inspection to quality_data tables.

    Tables affected:
    - QualityQcFa: matched by style + color + week, updates defect/status fields
    - InspectionDefect: synced from RevisionDefect (delete + recreate)
    - SecondsGeneral: UPSERT by style + color.name + week (common fields only)
    - SecondsA4: UPSERT by style + color + week (common fields only)

    Args:
        inspection: A closed InspectionData instance

    Returns:
        dict with keys: matched_records, synced_defects, status,
              total_defects, seconds_general, seconds_a4
    """
    if not inspection.is_closed:
        raise ValueError("Inspection must be closed before bridging.")

    with transaction.atomic():
        # ── SecondsGeneral UPSERT (always attempted, even on no QC match) ──
        sg_result = _bridge_seconds_general(inspection)

        # ── SecondsA4 UPSERT (always attempted, even on no QC match) ──
        sa4_result = _bridge_seconds_a4(inspection)

        # ── QualityQcFa matching by style + color + week ──
        qc_records = QualityQcFa.objects.filter(
            style__iexact=inspection.style,
            color=inspection.color,
            week=inspection.week,
        )

        if not qc_records.exists():
            return {
                "matched_records": 0,
                "synced_defects": 0,
                "status": "no_match",
                "total_defects": 0,
                "seconds_general": sg_result,
                "seconds_a4": sa4_result,
                "message": (
                    f"No QualityQcFa record found for "
                    f"style='{inspection.style}', color='{inspection.color}', "
                    f"week={inspection.week}"
                ),
            }

        # Aggregate defects from RevisionDefect
        defect_counts = _aggregate_defects(inspection)
        total_defects = sum(defect_counts.values())

        # Update each matching record
        synced = 0
        for qc_record in qc_records:
            qc_record.rejected = _calculate_rejected(
                qc_record.sample, defect_counts,
            )
            qc_record.accepted = max(
                0, qc_record.sample - qc_record.rejected,
            )
            qc_record.defects_total = total_defects
            qc_record.pass_or_fail = inspection.status
            qc_record.date_1 = inspection.closed_at.date().isoformat()
            qc_record.save()

            # Sync individual defect types to InspectionDefect
            synced += _sync_defect_types(qc_record, defect_counts)

        return {
            "matched_records": qc_records.count(),
            "synced_defects": synced,
            "status": "synced",
            "total_defects": total_defects,
            "seconds_general": sg_result,
            "seconds_a4": sa4_result,
        }


def _bridge_seconds_general(inspection: InspectionData) -> dict:
    """
    UPSERT a SecondsGeneral record with common fields from the inspection.

    Matches by (style, color.name, week). Fills date, week, style, color,
    and size. Production fields (produced, fixed, definitive, etc.) are
    NEVER overwritten — they stay at their existing values or default 0.

    Returns:
        dict with keys: created, updated, record_id
    """
    defaults = {
        "date": inspection.date.isoformat(),
        "size": inspection.size,
    }

    record, created = SecondsGeneral.objects.update_or_create(
        style=inspection.style,
        color=inspection.color.name,
        week=inspection.week,
        defaults=defaults,
    )

    # Sync garment defects to seconds defects where names overlap
    _sync_seconds_defects(record, inspection)

    return {
        "created": created,
        "updated": not created,
        "record_id": record.pk,
    }


def _bridge_seconds_a4(inspection: InspectionData) -> dict:
    """
    UPSERT a SecondsA4 record with common fields from the inspection.

    Matches by (style, color, week). Fills year, week, date, style, and
    color. Production fields (cut_num, cut_qty, sew_def, fab_def, etc.)
    are NEVER overwritten — they stay at existing values or 0.

    Uses get_or_create + conditional update to avoid overwriting
    production fields that lack DB defaults (SecondsA4 has many
    IntegerField without default=0).

    Returns:
        dict with keys: created, updated, record_id
    """
    record, created = SecondsA4.objects.get_or_create(
        style=inspection.style,
        color=inspection.color,
        week=inspection.week,
        defaults={
            "year": inspection.closed_at.year,
            "date": inspection.date.isoformat(),
            "line": "",
            "cut_num": 0,
            "cut_qty": 0,
            "first_quality_qty_sewing": 0,
            "sample": 0,
            "pass_field": 0,
            "fail_field": 0,
            "sew_def": 0,
            "fab_def": 0,
            "accepted": 0,
            "rejected": 0,
            "total_of_2ds": 0,
            "percentage_of_2ds": 0.0,
            "seconds_by_sew": 0,
            "seconds_by_fab": 0,
            "seconds_sew_a4": 0,
            "seconds_fab_a4": 0,
        },
    )

    if not created:
        # Only update common fields (never touch production fields)
        record.date = inspection.date.isoformat()
        record.save(update_fields=["date"])

    return {
        "created": created,
        "updated": not created,
        "record_id": record.pk,
    }


def _aggregate_defects(inspection: InspectionData) -> dict:
    """
    Aggregate RevisionDefect counts by defect type name.

    Returns:
        dict mapping defect type name → total count
    """
    counts = {}
    defects = RevisionDefect.objects.filter(
        inspection=inspection,
        defect_type__isnull=False,
    ).values_list('defect_type__name', 'defect_count')

    for defect_name, count in defects:
        counts[defect_name] = counts.get(defect_name, 0) + count

    return counts


def _calculate_rejected(sample: int, defect_counts: dict) -> int:
    """
    Calculate rejected count from defect data.

    Simple heuristic: if any defects exist, the sample is rejected.
    This can be refined with AQL logic later.
    """
    if not defect_counts:
        return 0
    return sum(defect_counts.values())


def _sync_defect_types(
    qc_record: QualityQcFa,
    defect_counts: dict,
) -> int:
    """
    Sync defect type counts to the InspectionDefect through table.

    Deletes existing defects for this QC record and recreates them
    from the aggregated counts.

    Returns:
        Number of defect records synced.
    """
    # Remove existing defect links for this inspection
    InspectionDefect.objects.filter(inspection=qc_record).delete()

    synced = 0
    for defect_name, amount in defect_counts.items():
        defect_type = DefectType.objects.filter(
            name=defect_name,
            is_active=True,
        ).first()

        if defect_type is None:
            continue

        InspectionDefect.objects.create(
            inspection=qc_record,
            defect_type=defect_type,
            amount=amount,
        )
        synced += 1

    return synced


def _sync_seconds_defects(
    sg_record: SecondsGeneral,
    inspection: InspectionData,
) -> int:
    """
    Sync garment defects to SecondsGeneralDefect where names overlap.

    Uses GARMENT_TO_SECONDS_DEFECT_MAP to translate garment defect type
    names (English) to seconds defect type names (Spanish). Only maps
    types that exist in both the garment DefectType table AND the
    SecondsGeneralDefectType table.

    Existing SecondsGeneralDefect records for this SecondsGeneral are
    deleted and recreated to keep the mapping clean.

    Returns:
        Number of SecondsGeneralDefect records created.
    """
    # Aggregate RevisionDefect counts by garment defect type name
    garment_counts = {}
    for rd in RevisionDefect.objects.filter(
        inspection=inspection,
        defect_type__isnull=False,
    ).select_related('defect_type'):
        name = rd.defect_type.name
        garment_counts[name] = garment_counts.get(name, 0) + rd.defect_count

    # Build lookup: seconds defect type name → SecondsGeneralDefectType instance
    mapped_names = set(GARMENT_TO_SECONDS_DEFECT_MAP.values())
    seconds_types = {
        st.name: st
        for st in SecondsGeneralDefectType.objects.filter(name__in=mapped_names)
    }

    # Delete existing defects for this SecondsGeneral record
    SecondsGeneralDefect.objects.filter(seconds_general=sg_record).delete()

    synced = 0
    for garment_name, amount in garment_counts.items():
        seconds_name = GARMENT_TO_SECONDS_DEFECT_MAP.get(garment_name)
        if seconds_name is None:
            continue

        seconds_type = seconds_types.get(seconds_name)
        if seconds_type is None:
            continue

        if amount <= 0:
            continue

        SecondsGeneralDefect.objects.create(
            seconds_general=sg_record,
            defect_type=seconds_type,
            amount=amount,
        )
        synced += 1

    return synced

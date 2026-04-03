"""
Inspection Bridge — Connect media_data inspections to quality_data tables.

When a tactile inspection is closed, this service:
1. Looks up the corresponding QualityQcFa record by style + color
2. Updates accepted/rejected/defects_total based on captured defects
3. Syncs RevisionDefect records into InspectionDefect (through table)

This bridges the gap between the touch capture interface (media_data)
and the QC reporting tables (quality_data).
"""

from django.db import transaction
from quality_data.models import (
    QualityQcFa,
    InspectionDefect,
    DefectType,
)
from media_data.models import InspectionData, RevisionDefect


def bridge_inspection(inspection: InspectionData) -> dict:
    """
    Sync a closed inspection to QualityQcFa.

    Flow:
    1. Find matching QualityQcFa record(s) by style and color
    2. Count defects by type from RevisionDefect
    3. Update or create QualityQcFa with defect totals
    4. Sync InspectionDefect through-table records

    Args:
        inspection: A closed InspectionData instance

    Returns:
        dict with keys: matched_records, synced_defects, status
    """
    if not inspection.is_closed:
        raise ValueError("Inspection must be closed before bridging.")

    with transaction.atomic():
        # Find matching QC records by style and color
        qc_records = QualityQcFa.objects.filter(
            style__iexact=inspection.style,
            color=inspection.color,
        )

        if not qc_records.exists():
            return {
                "matched_records": 0,
                "synced_defects": 0,
                "status": "no_match",
                "message": (
                    f"No QualityQcFa record found for "
                    f"style='{inspection.style}', color='{inspection.color}'"
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
            qc_record.save()

            # Sync individual defect types to InspectionDefect
            synced += _sync_defect_types(qc_record, defect_counts)

        return {
            "matched_records": qc_records.count(),
            "synced_defects": synced,
            "status": "synced",
            "total_defects": total_defects,
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

"""
dashboard_assemblers — Shared payload assembly for all 4 dashboard domains.

Each ``build_*_payload(kpis)`` function takes a dict of pre-computed KPI
data keyed by kpi_key, serializes each KPI through its registered serializer
(from ``dashboard_contracts``), and returns the full domain payload dict.

Usage::

    from quality_data.dashboard_assemblers import build_container_payload

    # Volatile: compute row-based KPIs → assemble
    kpi_data = {"executive_summary": calc_container_executive_summary(rows), ...}
    payload = build_container_payload(kpi_data)

    # Live: compute ORM aggregations → assemble
    aggregates = queryset.aggregate(...)
    kpi_data = {"executive_summary": [{"label": ..., "value": ...}], ...}
    payload = build_container_payload(kpi_data)

KPIs registered with ``serializer_path=None`` are passed through as-is
(raw dict is the canonical output contract).
"""

import importlib

from quality_data.dashboard_contracts import (
    CONTAINER_KPI_REGISTRY,
    SECONDS_A4_KPI_REGISTRY,
    SECONDS_GENERAL_KPI_REGISTRY,
    QCFA_KPI_REGISTRY,
)


def _resolve_serializer(serializer_path):
    """
    Import a serializer class from its dotted path.

    Args:
        serializer_path: E.g. ``"quality_data.serializers.KpiBarSerializer"``.

    Returns:
        The serializer class, or ``None`` if path is ``None``.
    """
    if serializer_path is None:
        return None
    parts = serializer_path.split(".")
    module_path = ".".join(parts[:-1])
    class_name = parts[-1]
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _serialize_kpi(data, serializer_cls, many):
    """
    Serialize a single KPI's data.

    Args:
        data: Raw KPI data (list of dicts or single dict).
        serializer_cls: DRF Serializer class, or ``None`` for passthrough.
        many: Whether the serializer expects ``many=True``.

    Returns:
        Serialized data, or raw data if serializer_cls is ``None``.
    """
    if serializer_cls is None:
        return data
    serializer = serializer_cls(data, many=many)
    return serializer.data


def _build_payload(kpis, registry):
    """
    Generic payload builder.

    For each entry in the registry:
      1. Look up the KPI data from the ``kpis`` dict.
      2. If missing, set the value to ``None``.
      3. Resolve the serializer class.
      4. Serialize (or passthrough).

    Args:
        kpis: Dict of pre-computed KPI data keyed by kpi_key.
        registry: List of ``(kpi_key, serializer_path, many)`` tuples.

    Returns:
        Dict with the full domain payload (serialized).
    """
    payload = {}
    for kpi_key, serializer_path, many in registry:
        data = kpis.get(kpi_key)
        if data is None:
            payload[kpi_key] = None
        else:
            serializer_cls = _resolve_serializer(serializer_path)
            payload[kpi_key] = _serialize_kpi(data, serializer_cls, many)
    return payload


# ─────────────────────────────────────────────────────────
# Domain-specific payload builders
# ─────────────────────────────────────────────────────────


def build_container_payload(kpis):
    """
    Assemble the full Container KPI payload.

    Args:
        kpis: Dict with keys matching ``CONTAINER_KPI_KEYS``.
              Each value is the pre-computed KPI data (list of dicts).

    Returns:
        Dict with all Container KPIs serialized.
    """
    return _build_payload(kpis, CONTAINER_KPI_REGISTRY)


def build_seconds_a4_payload(kpis):
    """
    Assemble the full Seconds A4 KPI payload.

    Args:
        kpis: Dict with keys matching ``SECONDS_A4_KPI_KEYS``.

    Returns:
        Dict with all Seconds A4 KPIs serialized.
    """
    return _build_payload(kpis, SECONDS_A4_KPI_REGISTRY)


def build_seconds_general_payload(kpis):
    """
    Assemble the full Seconds General KPI payload.

    Args:
        kpis: Dict with keys matching ``SECONDS_GENERAL_KPI_KEYS``.

    Returns:
        Dict with all Seconds General KPIs serialized.
    """
    return _build_payload(kpis, SECONDS_GENERAL_KPI_REGISTRY)


def build_qcfa_payload(kpis):
    """
    Assemble the full QC FA KPI payload.

    Args:
        kpis: Dict with keys matching ``QCFA_KPI_KEYS``.

    Returns:
        Dict with all QC FA KPIs serialized.
    """
    return _build_payload(kpis, QCFA_KPI_REGISTRY)

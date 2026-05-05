from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework import exceptions as rest_framework_exceptions
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Count, Case, When, F, FloatField
import pandas as pd
import numpy as np
import datetime
from quality_data.models import QualityQcFa, SecondsA4, SecondsGeneral, Container, ExcelSyncSession, InspectionDefect, Color
from excel_importer.handler_service import (
    load_and_clean,
)
from excel_importer.sheet_configs import (
    SHEET_NAMES,
    QC_FA_PLANT_REMAP,
    QC_FA_PLANT_NUMERIC_COLUMNS,
    QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
    QC_FA_CUSTOMER_REMAP,
    QC_FA_CUSTOMER_NUMERIC_COLUMNS,
    QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
    SECONDS_A4_REMAP,
    SECONDS_A4_NUMERIC_COLUMNS,
    SECONDS_GENERAL_REMAP,
    SECONDS_GENERAL_NUMERIC_COLUMNS,
    SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS,
    CONTAINER_REMAP,
    CONTAINER_NUMERIC_COLUMNS,
    CONTAINER_AMOUNT_DEFEACTS_FIELDS,
)
from excel_importer.sync_service import (
    create_session_from_dataframes,
    apply_session,
    reject_session,
)
from excel_importer.pivot_parsers import (
    parse_seconds_rework,
    parse_fabric_defects,
    parse_top_defects,
    parse_defects_by_style,
    parse_containers_by_state,
    DEFECT_LABEL_MAP,
)
from quality_data.corporate_xlsx_service import (
    CorporateXlsxReportService,
    EmptyCorporateXlsxDataError,
)
from quality_data.serializers import (
    KpiBarSerializer,
    KpiSeriesSerializer,
    KpiDonutSerializer,
    KpiHeatmapSerializer,
    KpiBarEnvelopeSerializer,
    KpiSeriesEnvelopeSerializer,
    ScalarMetricSerializer,
    FilterOptionsSerializer,
)

def _df_to_json_safe(df):
    """
    Convert a DataFrame to a list of dicts with JSON-serializable values.

    Uses vectorized pandas operations instead of row-by-row Python iteration.
    Handles: Timestamp → ISO date, NaN → None, numpy types → Python types.
    """
    if df is None or df.empty:
        return []

    # Work on a copy to avoid mutating the original
    df = df.copy()

    # Convert datetime columns to ISO date strings (vectorized)
    for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
        df[col] = df[col].dt.strftime('%Y-%m-%d')

    # Replace NaN/NaT with None for JSON compatibility. 
    # Must cast to object first, otherwise float columns convert None back to NaN
    df = df.astype(object).where(pd.notna(df), None)

    # Convert to dicts — pandas already handles numpy→Python type conversion
    return df.to_dict('records')


def _serialize_payload(serializer_cls, payload, many=False):
    """Serialize a payload using a DTO serializer class."""
    serializer = serializer_cls(payload, many=many)
    return serializer.data


def _serialize_envelope(envelope_serializer_cls, payload):
    """Serialize a `{data: [...]}` response using an envelope serializer class."""
    serializer = envelope_serializer_cls({"data": payload})
    return serializer.data


def _resolve_context_table_type(context_raw):
    """
    Map a context query parameter value to a QualityQcFa table_type.

    Args:
        context_raw: Raw string from query param (may be None, empty, or any case).

    Returns:
        'QFA' for plant (or omitted/empty), 'QFC' for customer.

    Raises:
        ValidationError if context is not a recognized value.
    """
    context = str(context_raw).strip().lower() if context_raw else "plant"
    if context == "":
        context = "plant"

    if context == "plant":
        return "QFA"
    elif context == "customer":
        return "QFC"
    else:
        raise rest_framework_exceptions.ValidationError({
            "context": f"Unsupported context '{context}'. Valid values: plant, customer."
        })

# ─────────────────────────────────────────────────────────
# Shared acceptance-rate and team-sanitization helpers
# ─────────────────────────────────────────────────────────

_valid_team_range = range(1, 37)


def _calculate_acceptance_rate(total_accepted, total_rejected):
    """
    Compute acceptance rate as accepted / (accepted + rejected) * 100.

    Returns a float rounded to 2 decimal places. Returns 0 when the
    denominator (accepted + rejected) is zero. Handles None inputs by
    treating them as 0.
    """
    accepted = total_accepted or 0
    rejected = total_rejected or 0
    denominator = accepted + rejected
    if denominator > 0:
        return round((accepted / denominator) * 100, 2)
    return 0


def _apply_team_sanitization_queryset(queryset):
    """
    Canonicalize team 60→6 via a `canonical_team` annotation, then keep
    only rows where canonical_team is within 1..36.

    After calling this, use `canonical_team` (not `team`) in values(),
    F() expressions, and group-bys. The raw `team` field preserves the
    original value; `canonical_team` holds the sanitized value.

    Returns the annotated and filtered queryset.
    """
    from django.db.models import Case, When, Value, IntegerField
    return queryset.annotate(
        canonical_team=Case(
            When(team=60, then=Value(6)),
            default=F('team'),
            output_field=IntegerField(),
        )
    ).filter(canonical_team__gte=1, canonical_team__lte=36)


def _qfc_conditional_denominator():
    """
    Return a Case/When expression for the defect rate denominator.

    For QFC (customer) records, the denominator is `accepted + rejected`.
    For all other records (e.g. QFA plant), it remains `sample`.

    Use this in aggregate() and annotate() calls where the denominator
    of the defect rate formula depends on table_type.
    """
    return Case(
        When(table_type='QFC', then=F('accepted') + F('rejected')),
        default=F('sample'),
        output_field=FloatField(),
    )


def _sanitize_team_dataframe(df):
    """
    Sanitize a pandas DataFrame by canonicalizing team 60→6 and then
    keeping only rows where the 'team' column value is within 1..36.

    Returns a filtered DataFrame (may be empty). Does NOT mutate the input.
    """
    if df is None or df.empty:
        return df
    df = df.copy()
    df['team'] = df['team'].replace(60, 6)
    return df[df['team'].isin(_valid_team_range)]


class Process(APIView):
    """
    Process an uploaded Excel file for preview (V2 workflow).

    Note: This endpoint only uses qc_fa_plant_df for parsing validation.
    The other 4 sheets are parsed but discarded because the real sync
    happens in ExcelConfirmView after user confirmation.

    This endpoint exists to support the upload → preview → confirm workflow.
    """
    parser_classes = [MultiPartParser]

    def post (self, request, filename, format = None):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=400)

        # Only _qc_fa_plant_df is used for validation in this endpoint.
        # The other sheets are parsed but not used here - they will be
        # processed in ExcelConfirmView after user confirms the preview.
        _ = load_and_clean(
            file_obj,
            QC_FA_PLANT_REMAP,
            QC_FA_PLANT_NUMERIC_COLUMNS,
            QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
            *SHEET_NAMES[0],
        )

        # Parse remaining sheets to validate file structure.
        # Results are discarded but parsing ensures the file is valid.
        load_and_clean(
            file_obj,
            QC_FA_CUSTOMER_REMAP,
            QC_FA_CUSTOMER_NUMERIC_COLUMNS,
            QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
            *SHEET_NAMES[1],
        )

        load_and_clean(
            file_obj,
            SECONDS_A4_REMAP,
            SECONDS_A4_NUMERIC_COLUMNS,
            None,
            *SHEET_NAMES[2],
        )

        load_and_clean(
            file_obj,
            SECONDS_GENERAL_REMAP,
            SECONDS_GENERAL_NUMERIC_COLUMNS,
            SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS,
            *SHEET_NAMES[3],
        )

        load_and_clean(
            file_obj,
            CONTAINER_REMAP,
            CONTAINER_NUMERIC_COLUMNS,
            CONTAINER_AMOUNT_DEFEACTS_FIELDS,
            *SHEET_NAMES[4],
        )


        return Response(status = 204)


# ─────────────────────────────────────────────────────────
# New V2 Views — Preview → Confirm → Apply workflow
# ─────────────────────────────────────────────────────────

class ExcelPreviewView(APIView):
    """
    Upload an Excel file and return a preview diff without modifying the database.

    POST /excel/preview/<filename>/
    Returns: session_id + preview summary (new, modified, warnings per sheet)
    """
    parser_classes = [MultiPartParser]

    def post(self, request, filename, format=None):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=http_status.HTTP_400_BAD_REQUEST)

        try:
            # Open the Excel file ONCE — all sheets are read from the same ExcelFile
            # object, avoiding 5 separate file open/parse cycles.
            # Gracefully fall back to per-sheet reading if ExcelFile creation fails
            # (e.g. invalid file, test mocks with /dev/null, etc.)
            try:
                excel_file = pd.ExcelFile(file_obj, engine='openpyxl')
            except Exception:
                excel_file = None

            # Parse all 5 sheets
            dataframes = {}

            qc_fa_plant_df = load_and_clean(
                file_obj, QC_FA_PLANT_REMAP, QC_FA_PLANT_NUMERIC_COLUMNS,
                QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS, *SHEET_NAMES[0],
                excel_file=excel_file,
            )
            dataframes["qc_fa_plant"] = _df_to_json_safe(qc_fa_plant_df)

            qc_fa_customer_df = load_and_clean(
                file_obj, QC_FA_CUSTOMER_REMAP, QC_FA_CUSTOMER_NUMERIC_COLUMNS,
                QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS, *SHEET_NAMES[1],
                excel_file=excel_file,
            )
            dataframes["qc_fa_customer"] = _df_to_json_safe(qc_fa_customer_df)

            seconds_a4_df = load_and_clean(
                file_obj, SECONDS_A4_REMAP, SECONDS_A4_NUMERIC_COLUMNS,
                None, *SHEET_NAMES[2],
                excel_file=excel_file,
            )
            dataframes["seconds_a4"] = _df_to_json_safe(seconds_a4_df)

            seconds_general_df = load_and_clean(
                file_obj, SECONDS_GENERAL_REMAP, SECONDS_GENERAL_NUMERIC_COLUMNS,
                SECONDS_GENERAL_AMOUNT_DEFEACTS_FIELDS, *SHEET_NAMES[3],
                excel_file=excel_file,
            )
            dataframes["seconds_general"] = _df_to_json_safe(seconds_general_df)

            container_df = load_and_clean(
                file_obj, CONTAINER_REMAP, CONTAINER_NUMERIC_COLUMNS,
                CONTAINER_AMOUNT_DEFEACTS_FIELDS, *SHEET_NAMES[4],
                excel_file=excel_file,
            )
            dataframes["container"] = _df_to_json_safe(container_df)

            # Create session with preview
            session = create_session_from_dataframes(dataframes)

            return Response({
                "session_id": session.pk,
                "status": session.status,
                "preview": {
                    "qc_fa_plant": session.qc_fa_plant_preview,
                    "qc_fa_customer": session.qc_fa_customer_preview,
                    "seconds_a4": session.seconds_a4_preview,
                    "seconds_general": session.seconds_general_preview,
                    "container": session.container_preview,
                },
                "warnings": session.warnings,
            }, status=http_status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to process Excel file: {str(e)}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )


class ExcelConfirmView(APIView):
    """
    Confirm and apply changes from a pending preview session.

    POST /excel/confirm/<int:session_id>/
    Returns: confirmation with summary of applied changes
    """

    def post(self, request, session_id, format=None):
        session = get_object_or_404(ExcelSyncSession, pk=session_id)

        if not session.is_pending:
            return Response(
                {"error": f"Session is already {session.status}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        try:
            apply_session(session)
            session.refresh_from_db()

            return Response({
                "session_id": session.pk,
                "status": session.status,
                "message": "Changes applied successfully",
            }, status=http_status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to apply changes: {str(e)}"},
                status=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExcelRejectView(APIView):
    """
    Reject a pending preview session — no changes are applied.

    DELETE /excel/reject/<int:session_id>/
    Returns: confirmation that session was rejected
    """

    def delete(self, request, session_id, format=None):
        session = get_object_or_404(ExcelSyncSession, pk=session_id)

        if not session.is_pending:
            return Response(
                {"error": f"Session is already {session.status}"},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        reject_session(session)

        return Response({
            "session_id": session.pk,
            "status": "rejected",
            "message": "Session rejected, no changes applied",
        }, status=http_status.HTTP_200_OK)


class KpiFilterMixin:
    """
    Mixin that provides queryset filtering based on query parameters.
    
    Supported filters:
        - date_range: date_1__gte / date_1__lte (format: "YYYY-MM-DD,YYYY-MM-DD")
        - week: week__exact
        - team: team__exact
        - style: style__iexact
        - color: color__name__iexact
        - customer: customer__iexact
        - batch: batch__exact
    
    For InspectionDefect-based querysets, filters are remapped to traverse
    the inspection FK relation (e.g., style becomes inspection__style).
    """

    # Maps filter names to (QualityQcFa field, is_numeric)
    FILTER_FIELD_MAP = {
        'date_range': ('date_1', False),
        'week': ('week', True),
        'team': ('team', True),
        'line_code': ('line_code', False),
        'style': ('style', False),
        'color': ('color__name', False),
        'customer': ('customer', False),
        'batch': ('batch', True),
    }

    @staticmethod
    def _parse_date_param(raw_value, field_name):
        if raw_value is None:
            return None

        value = str(raw_value).strip()
        if not value:
            return None

        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            raise rest_framework_exceptions.ValidationError({
                field_name: 'Invalid date. Use YYYY-MM-DD.'
            })

    @classmethod
    def _parse_date_range_param(cls, raw_value, field_name='date_range'):
        value = (raw_value or '').strip()
        if not value:
            return None, None

        parts = [part.strip() for part in value.split(',')]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise rest_framework_exceptions.ValidationError({
                field_name: 'Invalid date_range. Use YYYY-MM-DD,YYYY-MM-DD.'
            })

        from_date = cls._parse_date_param(parts[0], field_name)
        to_date = cls._parse_date_param(parts[1], field_name)
        cls._validate_date_order(from_date, to_date, field_name)
        return from_date, to_date

    @classmethod
    def parse_required_date_bounds(
        cls,
        query_params,
        from_field='date_from',
        to_field='date_to',
    ):
        from_raw = query_params.get(from_field)
        to_raw = query_params.get(to_field)

        missing_errors = {}
        if from_raw is None or not str(from_raw).strip():
            missing_errors[from_field] = 'This query parameter is required.'
        if to_raw is None or not str(to_raw).strip():
            missing_errors[to_field] = 'This query parameter is required.'

        if missing_errors:
            raise rest_framework_exceptions.ValidationError(missing_errors)

        from_date = cls._parse_date_param(from_raw, from_field)
        to_date = cls._parse_date_param(to_raw, to_field)
        cls._validate_date_order(from_date, to_date, (from_field, to_field))
        return from_date, to_date

    @staticmethod
    def _validate_date_order(from_date, to_date, field_name='date_range'):
        if from_date and to_date and from_date > to_date:
            if isinstance(field_name, (tuple, list)):
                raise rest_framework_exceptions.ValidationError({
                    name: "Invalid date range. Start date must be on or before end date."
                    for name in field_name
                })
            raise rest_framework_exceptions.ValidationError({
                field_name: "Invalid date range. Start date must be on or before end date."
            })

    def _apply_date_range_filter(self, queryset, field_name):
        date_range = self.request.query_params.get('date_range')
        if date_range is None:
            return queryset

        from_date, to_date = self._parse_date_range_param(date_range, 'date_range')
        if from_date:
            queryset = queryset.filter(**{f'{field_name}__gte': from_date.isoformat()})
        if to_date:
            queryset = queryset.filter(**{f'{field_name}__lte': to_date.isoformat()})
        return queryset

    def _get_filter_prefix(self, queryset):
        """
        Determine the filter prefix needed based on the queryset model.
        For InspectionDefect, we need to traverse inspection__ FK.
        """
        model_name = queryset.model._meta.model_name
        if model_name == 'inspectiondefect':
            return 'inspection__'
        return ''

    def _apply_context_filter(self, queryset, prefix):
        """
        Apply context filter to isolate QFA (Plant) or QFC (Customer) data.

        Supported values:
            - 'plant'    → table_type='QFA'
            - 'customer' → table_type='QFC'
            - omitted/empty → defaults to 'QFA' (plant)

        Raises:
            ValidationError if context value is unsupported.
        """
        context_raw = self.request.query_params.get('context')
        table_type = _resolve_context_table_type(context_raw)
        return queryset.filter(**{f'{prefix}table_type': table_type})

    def get_filtered_queryset(self, queryset):
        """
        Apply filters from query params to the given queryset.
        
        Args:
            queryset: Django QuerySet to filter
            
        Returns:
            Filtered QuerySet (or complete queryset if no filters applied)
        """
        request = self.request
        filters = {}
        prefix = self._get_filter_prefix(queryset)

        # context: plant → QFA, customer → QFC (applied before other filters)
        queryset = self._apply_context_filter(queryset, prefix)

        # date_range: "start_date,end_date" → date_1__gte, date_1__lte
        date_range = request.query_params.get('date_range')
        if date_range is not None:
            start_date, end_date = self._parse_date_range_param(date_range, 'date_range')
            field = f'{prefix}date_1'
            if start_date:
                filters[f'{field}__gte'] = start_date.isoformat()
            if end_date:
                filters[f'{field}__lte'] = end_date.isoformat()

        # week: exact integer match
        week = request.query_params.get('week')
        if week:
            try:
                filters[f'{prefix}week__exact'] = int(week)
            except ValueError:
                raise rest_framework_exceptions.ValidationError({
                    'week': 'Invalid value. It must be an integer.'
                })

        # team: exact integer match
        team = request.query_params.get('team')
        if team:
            try:
                filters[f'{prefix}team__exact'] = int(team)
            except ValueError:
                raise rest_framework_exceptions.ValidationError({
                    'team': 'Invalid value. It must be an integer.'
                })

        # line_code: exact string match (dual-line filter)
        line_code = request.query_params.get('line_code')
        if line_code:
            filters[f'{prefix}line_code__exact'] = str(line_code).strip()

        # style: exact match (optimized for B-Tree index)
        style = request.query_params.get('style')
        if style:
            filters[f'{prefix}style__exact'] = style

        # color: foreign key lookup via color__name (exact match for B-Tree index)
        color = request.query_params.get('color')
        if color:
            filters[f'{prefix}color__name__exact'] = color

        # customer: exact match (optimized for B-Tree index)
        customer = request.query_params.get('customer')
        if customer:
            filters[f'{prefix}customer__exact'] = customer

        # batch: exact integer match
        batch = request.query_params.get('batch')
        if batch:
            try:
                filters[f'{prefix}batch__exact'] = int(batch)
            except ValueError:
                raise rest_framework_exceptions.ValidationError({
                    'batch': 'Invalid value. It must be an integer.'
                })

        if filters:
            queryset = queryset.filter(**filters)

        # Global dual-line filter: only for QualityQcFa and InspectionDefect models.
        # When include_dual_lines is not 'true' and no explicit line_code is given,
        # exclude dual-line rows (line_code IS NULL). Explicit line_code takes
        # precedence — no extra exclusion is added.
        model_name = queryset.model._meta.model_name
        if model_name in ('qualityqcfa', 'inspectiondefect'):
            include_raw = request.query_params.get('include_dual_lines', '').strip().lower()
            include_dual_lines = include_raw == 'true'
            explicit_line_code = bool(request.query_params.get('line_code', '').strip())
            if not include_dual_lines and not explicit_line_code:
                queryset = queryset.filter(**{f'{prefix}line_code__isnull': True})

        return queryset

    def _apply_line_grouped_display(self, queryset, team_field='canonical_team'):
        """
        For line-grouped KPI views: annotate display_line, sort_team, and
        sort_is_dual for presentation ordering.

        Row inclusion/exclusion is now handled globally by get_filtered_queryset()
        via the include_dual_lines toggle. This method is presentation-only.

        - Annotates display_line = COALESCE(line_code, CAST(team_field AS text)).
        - Annotates sort_team and sort_is_dual for stable ordering.

        Returns (queryset, include_dual_lines_bool).
        """
        from django.db.models import Case, When, Value, CharField
        from django.db.models.functions import Cast

        include_raw = self.request.query_params.get('include_dual_lines', '').strip().lower()
        include_dual_lines = include_raw == 'true'

        queryset = queryset.annotate(
            sort_team=F(team_field),
            sort_is_dual=Case(
                When(line_code__isnull=False, then=1),
                default=0,
            ),
            display_line=Case(
                When(line_code__isnull=False, then=F('line_code')),
                default=Cast(F(team_field), output_field=CharField()),
                output_field=CharField(),
            )
        )
        return queryset, include_dual_lines


# ─────────────────────────────────────────────────────────
# Grupo 3 - KPIs Defectos Endpoints
# ─────────────────────────────────────────────────────────

class TopDefectsView(KpiFilterMixin, APIView):
    """
    GET /api/kpis/top-defects/

    Returns top 10 defect types by total amount (SUM of amount).
    Source: InspectionDefect → defect_type.name

    Response: [{"label": "Loose Thread", "value": 234}, ...]
    """

    def get(self, request):
        queryset = InspectionDefect.objects.all()
        queryset = self.get_filtered_queryset(queryset)

        aggregated = (
            queryset
            .values(defect_type_name=F('defect_type__name'))
            .annotate(total=Sum('amount'))
            .order_by('-total')[:10]
        )

        result = [
            {"label": item['defect_type_name'], "value": item['total']}
            for item in aggregated
        ]

        dto_data = _serialize_payload(KpiBarSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)


class FabricDefectsView(KpiFilterMixin, APIView):
    """
    GET /api/kpis/fabric-defects/

    Returns SUM of each fabric defect column from SecondsGeneral.
    Columns: corrido_2, barre, otros_3, degradacion, bordados

    Response: [{"label": "Corrido", "value": 45}, {"label": "Barre", "value": 23}, ...]

    Supports filters:
        - date_range: "start_date,end_date" → date__gte, date__lte
        - week: week__exact
    """

    def get(self, request):
        from quality_data.models import SecondsGeneralDefect
        queryset = SecondsGeneral.objects.all()
        queryset = self._apply_date_range_filter(queryset, 'date')

        week = request.query_params.get('week')
        if week:
            try:
                week = int(week)
            except ValueError:
                return Response(
                    {"detail": "Invalid 'week' parameter. It must be an integer."},
                    status=http_status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(week__exact=week)

        fabric_defect_names = ["corrido_2", "barre", "otros_3", "degradacion", "bordados"]

        aggregated = (
            SecondsGeneralDefect.objects
            .filter(
                seconds_general__in=queryset,
                defect_type__name__in=fabric_defect_names,
            )
            .values(defect_name=F("defect_type__name"))
            .annotate(total=Sum("amount"))
        )

        result_map = {item["defect_name"]: item["total"] or 0 for item in aggregated}

        label_map = {
            "corrido_2": "Corrido",
            "barre": "Barre",
            "otros_3": "Otros",
            "degradacion": "Degradación",
            "bordados": "Bordados",
        }

        result = [
            {"label": label_map[name], "value": result_map.get(name, 0)}
            for name in fabric_defect_names
        ]

        dto_data = _serialize_payload(KpiBarSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)


class DefectsByStyleTypeView(KpiFilterMixin, APIView):
    """
    GET /api/kpis/defects-by-style-type/

    Returns heatmap data: style × defect_type.name with SUM(amount).
    Limited to top 5 styles and top 5 defect types to avoid overload.

    Source: InspectionDefect → JOIN QualityQcFa (for style)

    Response: [{"x": "Style-2", "y": "Loose Thread", "value": 45}, ...]
    """

    def get(self, request):
        # Get filtered queryset first
        queryset = self.get_filtered_queryset(InspectionDefect.objects.all())

        # Get top 5 styles by total defect amount (from filtered data)
        top_styles = (
            queryset
            .values(style_name=F('inspection__style'))
            .annotate(total=Sum('amount'))
            .order_by('-total')[:5]
        )
        top_style_names = [item['style_name'] for item in top_styles]

        # Get top 5 defect types by total amount (from filtered data)
        top_defect_types = (
            queryset
            .values(defect_type_name=F('defect_type__name'))
            .annotate(total=Sum('amount'))
            .order_by('-total')[:5]
        )
        top_defect_type_names = [item['defect_type_name'] for item in top_defect_types]

        # Filter the filtered queryset by top styles and defect types
        queryset = queryset.filter(
            inspection__style__in=top_style_names,
            defect_type__name__in=top_defect_type_names,
        )

        # Aggregate by style × defect_type
        aggregated = (
            queryset
            .values(style_name=F('inspection__style'), defect_type_name=F('defect_type__name'))
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        result = [
            {"x": item['style_name'], "y": item['defect_type_name'], "value": item['total']}
            for item in aggregated
        ]

        dto_data = _serialize_payload(KpiHeatmapSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)


class DefectCompositionView(KpiFilterMixin, APIView):
    """
    GET /api/kpis/defect-composition/

    Returns donut-chart-ready composition of defect types.
    Source: InspectionDefect → defect_type.name
    Grouped by defect_type__name, SUM(amount).
    Sorted by value DESC, name ASC. Excludes zero totals.

    Response: [{ "name": "Loose Thread", "value": 234 }, ...]
    """

    def get(self, request):
        queryset = InspectionDefect.objects.all()
        queryset = self.get_filtered_queryset(queryset)

        aggregated = (
            queryset
            .values(defect_type_name=F('defect_type__name'))
            .annotate(total=Sum('amount'))
            .filter(total__gt=0)
            .order_by('-total', 'defect_type_name')
        )

        result = [
            {"name": item['defect_type_name'], "value": item['total']}
            for item in aggregated
        ]

        dto_data = _serialize_payload(KpiDonutSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)


class DefectTrendTop3View(KpiFilterMixin, APIView):
    """
    GET /api/kpis/defect-trend-top-3/

    Returns up to 3 weekly trend series for the top 3 defect types.
    Source: InspectionDefect → defect_type.name
    Steps:
      1. Pick top 3 defect types by filtered SUM(amount).
      2. For each, aggregate weekly totals (inspection__week).
      3. Build dense series: every filtered week present, y=0 for absent.
    Weeks are ascending. Returns [] when no positive defect amounts.

    Response: [
      { "name": "Loose Thread", "data": [{ "x": 1, "y": 10 }, ...] },
      ...
    ]
    """

    def get(self, request):
        queryset = InspectionDefect.objects.all()
        queryset = self.get_filtered_queryset(queryset)

        # Step 1: Top 3 defect types by SUM(amount), filtered to positive totals
        top_defects = (
            queryset
            .values(defect_type_name=F('defect_type__name'))
            .annotate(total=Sum('amount'))
            .filter(total__gt=0)
            .order_by('-total', 'defect_type_name')[:3]
        )

        top_names = [item['defect_type_name'] for item in top_defects]
        if not top_names:
            return Response([], status=http_status.HTTP_200_OK)

        # Step 2: Distinct filtered weeks (ascending)
        filtered_weeks = sorted(
            queryset
            .values_list('inspection__week', flat=True)
            .distinct()
        )

        # Step 3: Weekly aggregation per top-defect type
        weekly_aggregates = (
            queryset
            .filter(defect_type__name__in=top_names)
            .values(defect_type_name=F('defect_type__name'), week=F('inspection__week'))
            .annotate(weekly_total=Sum('amount'))
            .order_by('defect_type_name', 'week')
        )

        # Build dense series: one per top_defect, all weeks present
        series_by_name = {}
        for agg in weekly_aggregates:
            name = agg['defect_type_name']
            week = agg['week']
            weekly_total = agg['weekly_total']
            if name not in series_by_name:
                series_by_name[name] = {}
            series_by_name[name][week] = weekly_total or 0

        result = []
        for name in top_names:
            data = [
                {"x": week, "y": series_by_name.get(name, {}).get(week, 0)}
                for week in filtered_weeks
            ]
            result.append({"name": name, "data": data})

        dto_data = _serialize_payload(KpiSeriesSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# Grupo 4 - KPIs Operativos Endpoints
# ─────────────────────────────────────────────────────────

class PassRejectDistributionView(KpiFilterMixin, APIView):
    """
    GET /api/kpis/pass-reject-distribution/

    Source: QualityQcFa
    GROUP BY pass_or_fail: COUNT

    Response: [{"name": "PASS", "value": 85}, {"name": "REJECT", "value": 15}]
    """

    def get(self, request):
        queryset = self.get_filtered_queryset(QualityQcFa.objects.all())

        aggregated = (
            queryset
            .values(pof=F('pass_or_fail'))
            .annotate(count=Count('id'))
            .order_by('pof')
        )

        result = [
            {"name": item['pof'], "value": item['count']}
            for item in aggregated
        ]

        dto_data = _serialize_payload(KpiDonutSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)


class RejectedEvolutionView(KpiFilterMixin, APIView):
    """
    GET /api/kpis/rejected-evolution/

    Source: QualityQcFa
    GROUP BY week: SUM(rejected)
    Ordered by week

    Response: [{"name": "Rejected", "data": [{"x": 1, "y": 23}, ...]}]
    """

    def get(self, request):
        queryset = self.get_filtered_queryset(QualityQcFa.objects.all())

        aggregated = (
            queryset
            .values(week_num=F('week'))
            .annotate(total_rejected=Sum('rejected'))
            .order_by('week_num')
        )

        result = [{
            "name": "Rejected",
            "data": [
                {"x": item['week_num'], "y": item['total_rejected'] or 0}
                for item in aggregated
            ]
        }]

        dto_data = _serialize_payload(KpiSeriesSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)


class ContainersByStateView(KpiFilterMixin, APIView):
    """
    GET /api/kpis/containers-by-state/

    Source: Container
    Group by percentage_pass ranges:
        - "< 80%"
        - "80-90%"
        - "90-95%"
        - "> 95%"

    Response: [{"name": "< 80%", "value": 3}, {"name": "80-90%", "value": 12}, ...]
    """

    def get(self, request):
        queryset = Container.objects.all()

        # Apply customer filter if provided (Container has customer field)
        customer = request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(customer__exact=customer)

        date_range_raw = request.query_params.get('date_range')
        if date_range_raw is not None and date_range_raw.strip():
            from_date, to_date = self._parse_date_range_param(date_range_raw, 'date_range')
        else:
            from_date = self._parse_date_param(request.query_params.get('from_date'), 'from_date')
            to_date = self._parse_date_param(request.query_params.get('to_date'), 'to_date')
            self._validate_date_order(from_date, to_date, ('from_date', 'to_date'))

        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)

        # Use Case/When for range grouping
        from django.db.models import IntegerField

        aggregated = (
            queryset
            .annotate(
                range_bucket=Case(
                    When(percentage_pass__lt=80, then=1),
                    When(percentage_pass__gte=80, percentage_pass__lt=90, then=2),
                    When(percentage_pass__gte=90, percentage_pass__lte=95, then=3),
                    When(percentage_pass__gt=95, then=4),
                    output_field=IntegerField(),
                )
            )
            .values('range_bucket')
            .annotate(count=Count('id'))
        )

        # Build result with proper labels
        range_labels = {
            1: "< 80%",
            2: "80-90%",
            3: "90-95%",
            4: "> 95%",
        }

        result = [
            {"name": range_labels[item['range_bucket']], "value": item['count']}
            for item in aggregated
        ]

        # Ensure all ranges are present (even if 0)
        all_ranges = ["< 80%", "80-90%", "90-95%", "> 95%"]
        result_dict = {r["name"]: r["value"] for r in result}
        result = [{"name": r, "value": result_dict.get(r, 0)} for r in all_ranges]

        dto_data = _serialize_payload(KpiDonutSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)

class DefectRateView(KpiFilterMixin, APIView):
    """
    GET /api/kpis/defect-rate/

    Source: QualityQcFa
    Global average: SUM(defects_total) / SUM(sample) * 100
    For QFC (customer) records, denominator is SUM(accepted + rejected)
    instead of SUM(sample).

    Response: {"label": "Defect Rate", "value": 2.34}
    If total sample = 0 → value = 0
    """

    def get(self, request):
        queryset = self.get_filtered_queryset(QualityQcFa.objects.all())

        # Conditional denominator: QFC uses accepted+rejected, QFA uses sample
        aggregated = queryset.aggregate(
            total_defects=Sum('defects_total'),
            total_denominator=Sum(_qfc_conditional_denominator()),
        )

        total_defects = aggregated['total_defects'] or 0
        total_denominator = aggregated['total_denominator'] or 0

        value = 0
        if total_denominator > 0:
            value = round((total_defects / total_denominator) * 100, 2)

        result = _serialize_payload(
            ScalarMetricSerializer,
            {"label": "Defect Rate", "value": value},
            many=False,
        )

        return Response(result, status=http_status.HTTP_200_OK)


class CorporateXlsxReportView(KpiFilterMixin, APIView):
    def get(self, request):
        date_from, date_to = self.parse_required_date_bounds(request.query_params)
        service = CorporateXlsxReportService()

        try:
            artifact = service.generate(date_from, date_to)
        except EmptyCorporateXlsxDataError as error:
            return Response(
                {"error": str(error)},
                status=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        response = HttpResponse(
            artifact.file_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{artifact.filename}"'
        return response


# ─────────────────────────────────────────────────────────
# Grupo 2 - KPIs Rendimiento Endpoints
# ─────────────────────────────────────────────────────────

class KpiViewSet(KpiFilterMixin, ViewSet):
    """
    KPI endpoints for rendimiento (performance) metrics.

    Endpoints:
        - GET /api/kpis/ac-re-rate-by-line/     → pass/fail count by team
        - GET /api/kpis/seconds-rework/         → sewing vs fabric rework seconds by week
        - GET /api/kpis/performance-by-customer/ → acceptance rate by customer
        - GET /api/kpis/performance-by-line/     → acceptance rate by team
    """

    def get_quality_queryset(self):
        """Return base QualityQcFa queryset with filters applied."""
        queryset = QualityQcFa.objects.all()
        return self.get_filtered_queryset(queryset)

    @action(detail=False, methods=['get'], url_path='ac-re-rate-by-line')
    def ac_re_rate_by_line(self, request):
        """
        GET /api/kpis/ac-re-rate-by-line/

        Source: QualityQcFa
        GROUP BY display_line × pass_or_fail: COUNT of records.
        Teams are canonicalized (60→6) and filtered to 1..36.
        Dual lines show exact labels when include_dual_lines=true.

        Response: [{"label": "Line 1 - PASS", "value": 45}, {"label": "Line 1 - REJECT", "value": 5}, ...]
        """
        queryset = self.get_quality_queryset()

        # Sanitize: canonicalize 60→6, exclude teams outside 1..36
        queryset = _apply_team_sanitization_queryset(queryset)

        # Apply dual-line display: filter/annotate for line-grouped output
        queryset, _ = self._apply_line_grouped_display(queryset)

        aggregated = (
            queryset
            .values(
                line_label=F('display_line'),
                pof=F('pass_or_fail'),
                sort_team=F('sort_team'),
                sort_is_dual=F('sort_is_dual'),
            )
            .annotate(count=Count('id'))
            .order_by('sort_team', 'sort_is_dual', 'line_label', 'pof')
        )

        result = [
            {"label": f"{item['line_label']} - {item['pof']}", "value": item['count']}
            for item in aggregated
        ]

        dto_data = _serialize_payload(KpiBarSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='seconds-rework')
    def seconds_rework(self, request):
        """
        GET /api/kpis/seconds-rework/

        Source: SecondsA4
        GROUP BY week: SUM(seconds_by_sew), SUM(seconds_by_fab).

        Returns 2 series:
            - {name: "Sewing", data: [{x: 1, y: 12.3}, ...]}
            - {name: "Fabric", data: [{x: 1, y: 5.6}, ...]}

        Supports filters:
            - date_range: "start_date,end_date" → date__gte, date__lte
        """
        queryset = SecondsA4.objects.all()

        queryset = self._apply_date_range_filter(queryset, 'date')

        aggregated = (
            queryset
            .values(week_num=F('week'))
            .annotate(
                total_sew=Sum('seconds_by_sew'),
                total_fab=Sum('seconds_by_fab'),
            )
            .order_by('week_num')
        )

        sewing_data = [{"x": item['week_num'], "y": item['total_sew'] or 0} for item in aggregated]
        fabric_data = [{"x": item['week_num'], "y": item['total_fab'] or 0} for item in aggregated]

        result = [
            {"name": "Sewing", "data": sewing_data},
            {"name": "Fabric", "data": fabric_data},
        ]

        dto_data = _serialize_payload(KpiSeriesSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='performance-by-customer')
    def performance_by_customer(self, request):
        """
        GET /api/kpis/performance-by-customer/

        Source: QualityQcFa
        GROUP BY customer: accepted / (accepted + rejected) * 100.

        Response: [{"label": "Customer X", "value": 92.5}, ...]
        """
        queryset = self.get_quality_queryset()

        aggregated = (
            queryset
            .values(customer_name=F('customer'))
            .annotate(
                total_accepted=Sum('accepted'),
                total_rejected=Sum('rejected'),
            )
            .order_by('customer_name')
        )

        result = [
            {
                "label": item['customer_name'],
                "value": _calculate_acceptance_rate(
                    item['total_accepted'], item['total_rejected']
                ),
            }
            for item in aggregated
        ]

        dto_data = _serialize_payload(KpiBarSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='performance-by-line')
    def performance_by_line(self, request):
        """
        GET /api/kpis/performance-by-line/

        Source: QualityQcFa
        GROUP BY display_line: accepted / (accepted + rejected) * 100.
        Teams are canonicalized (60→6) and filtered to 1..36.
        Dual lines show exact labels when include_dual_lines=true.

        Response: [{"label": "Line 1", "value": 95.2}, ...]
        """
        queryset = self.get_quality_queryset()

        # Sanitize: canonicalize 60→6, exclude teams outside 1..36
        queryset = _apply_team_sanitization_queryset(queryset)

        # Apply dual-line display: filter/annotate for line-grouped output
        queryset, _ = self._apply_line_grouped_display(queryset)

        aggregated = (
            queryset
            .values(
                line_label=F('display_line'),
                sort_team=F('sort_team'),
                sort_is_dual=F('sort_is_dual'),
            )
            .annotate(
                total_accepted=Sum('accepted'),
                total_rejected=Sum('rejected'),
            )
            .order_by('sort_team', 'sort_is_dual', 'line_label')
        )

        result = [
            {
                "label": item['line_label'],
                "value": _calculate_acceptance_rate(
                    item['total_accepted'], item['total_rejected']
                ),
            }
            for item in aggregated
        ]

        dto_data = _serialize_payload(KpiBarSerializer, result, many=True)
        return Response(dto_data, status=http_status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────
# Grupo 1 - KPIs AQL Endpoints
# ─────────────────────────────────────────────────────────

class AqlKpiViewSet(ViewSet, KpiFilterMixin):
    """
    KPI endpoints for AQL (Acceptable Quality Limit) metrics.

    All endpoints support KpiFilterMixin query parameters:
        - date_range: "YYYY-MM-DD,YYYY-MM-DD"
        - week: integer
        - team: integer
        - style: string (icontains)
        - color: string (icontains)
        - customer: string (icontains)
        - batch: integer
    """

    def get_queryset(self):
        return QualityQcFa.objects.all()

    @action(detail=False, methods=['get'], url_path='aql-by-team')
    def aql_by_team(self, request):
        """
        GET /api/kpis/aql/aql-by-team/

        Returns AQL percentage grouped by team (line).
        Formula: SUM(defects_total) / SUM(conditional_denominator) * 100
        For QFC records, denominator is SUM(accepted + rejected); for QFA, SUM(sample).
        Dual lines show exact labels when include_dual_lines=true.
        """
        queryset = self.get_filtered_queryset(self.get_queryset())

        # Apply dual-line display: filter/annotate for line-grouped output
        # Use raw 'team' as fallback since AQL does not canonicalize
        queryset, _ = self._apply_line_grouped_display(queryset, team_field='team')

        if not queryset.exists():
            return Response(_serialize_envelope(KpiBarEnvelopeSerializer, []))

        # GROUP BY display_line: SUM(defects_total) / SUM(denominator) * 100
        # Denominator is conditional: QFC uses accepted+rejected, QFA uses sample
        annotated = (
            queryset
            .values(
                'display_line',
                sort_team=F('sort_team'),
                sort_is_dual=F('sort_is_dual'),
            )
            .annotate(
                total_defects=Sum('defects_total'),
                total_denominator=Sum(_qfc_conditional_denominator()),
            )
            .order_by('sort_team', 'sort_is_dual', 'display_line')
        )

        result = []
        for row in annotated:
            denominator = row['total_denominator'] or 0
            defects = row['total_defects'] or 0
            if denominator > 0:
                aql = (defects / denominator) * 100
            else:
                aql = 0.0
            result.append({
                "label": str(row['display_line']),
                "value": round(aql, 2),
            })

        dto_data = _serialize_payload(KpiBarSerializer, result, many=True)
        return Response(_serialize_envelope(KpiBarEnvelopeSerializer, dto_data))

    @action(detail=False, methods=['get'], url_path='aql-by-style')
    def aql_by_style(self, request):
        """
        GET /api/kpis/aql-by-style/

        Returns AQL percentage grouped by style.
        Formula: SUM(defects_total) / SUM(conditional_denominator) * 100
        For QFC records, denominator is SUM(accepted + rejected); for QFA, SUM(sample).
        """
        queryset = self.get_filtered_queryset(self.get_queryset())

        if not queryset.exists():
            return Response(_serialize_envelope(KpiBarEnvelopeSerializer, []))

        # GROUP BY style: SUM(defects_total) / SUM(denominator) * 100
        # Denominator is conditional: QFC uses accepted+rejected, QFA uses sample
        annotated = (
            queryset
            .values('style')
            .annotate(
                total_defects=Sum('defects_total'),
                total_denominator=Sum(_qfc_conditional_denominator()),
            )
        )

        result = []
        for row in annotated:
            denominator = row['total_denominator'] or 0
            defects = row['total_defects'] or 0
            if denominator > 0:
                aql = (defects / denominator) * 100
            else:
                aql = 0.0
            result.append({
                "label": row['style'],
                "value": round(aql, 2),
            })

        # Sort by value descending
        result.sort(key=lambda x: x['value'], reverse=True)

        dto_data = _serialize_payload(KpiBarSerializer, result, many=True)
        return Response(_serialize_envelope(KpiBarEnvelopeSerializer, dto_data))

    @action(detail=False, methods=['get'], url_path='aql-weekly')
    def aql_weekly(self, request):
        """
        GET /api/kpis/aql-weekly/

        Returns weekly AQL trend with trend line.
        Formula: SUM(defects_total) / SUM(conditional_denominator) * 100
        For QFC records, denominator is SUM(accepted + rejected); for QFA, SUM(sample).
        """
        queryset = self.get_filtered_queryset(self.get_queryset())

        if not queryset.exists():
            return Response(_serialize_envelope(KpiSeriesEnvelopeSerializer, []))

        # GROUP BY week: SUM(defects_total) / SUM(denominator) * 100
        # Denominator is conditional: QFC uses accepted+rejected, QFA uses sample
        annotated = (
            queryset
            .values('week')
            .annotate(
                total_defects=Sum('defects_total'),
                total_denominator=Sum(_qfc_conditional_denominator()),
            )
            .order_by('week')
        )

        # Build series data
        aql_data = []
        for row in annotated:
            week = row['week']
            total_defects = row['total_defects'] or 0
            total_denominator = row['total_denominator'] or 0
            aql = (total_defects / total_denominator * 100) if total_denominator > 0 else 0.0
            aql_data.append({"x": week, "y": round(aql, 2)})

        if not aql_data:
            return Response(_serialize_envelope(KpiSeriesEnvelopeSerializer, []))

        # Calculate simple trend line (average of differences)
        if len(aql_data) >= 2:
            differences = []
            for i in range(1, len(aql_data)):
                diff = aql_data[i]['y'] - aql_data[i - 1]['y']
                differences.append(diff)
            slope = sum(differences) / len(differences) if differences else 0
        else:
            slope = 0

        # Build trend line series (same x values, linear interpolation)
        trend_data = []
        if len(aql_data) >= 2:
            first_x = aql_data[0]['x']
            first_y = aql_data[0]['y']
            for point in aql_data:
                trend_y = first_y + slope * (point['x'] - first_x)
                trend_data.append({"x": point['x'], "y": round(trend_y, 2)})
        else:
            # Single point - trend = same value
            trend_data = [{"x": aql_data[0]['x'], "y": aql_data[0]['y']}]

        aql_series = _serialize_payload(
            KpiSeriesSerializer,
            {"name": "AQL", "data": aql_data},
            many=False,
        )
        trend_series = _serialize_payload(
            KpiSeriesSerializer,
            {"name": "Trend", "data": trend_data},
            many=False,
        )
        return Response(
            _serialize_envelope(KpiSeriesEnvelopeSerializer, [aql_series, trend_series])
        )

    @action(detail=False, methods=['get'], url_path='audited-pieces')
    def audited_pieces(self, request):
        """
        GET /api/kpis/audited-pieces/

        Returns weekly total of audited pieces (SUM of sample).
        """
        queryset = self.get_filtered_queryset(self.get_queryset())

        if not queryset.exists():
            return Response(_serialize_envelope(KpiSeriesEnvelopeSerializer, []))

        # GROUP BY week: SUM(sample)
        annotated = (
            queryset
            .values('week')
            .annotate(total_sample=Sum('sample'))
            .order_by('week')
        )

        pieces_data = []
        for row in annotated:
            pieces_data.append({
                "x": row['week'],
                "y": row['total_sample'] or 0
            })

        pieces_series = _serialize_payload(
            KpiSeriesSerializer,
            {"name": "Pieces", "data": pieces_data},
            many=False,
        )
        return Response(_serialize_envelope(KpiSeriesEnvelopeSerializer, [pieces_series]))


# ─────────────────────────────────────────────────────────
# Volatile KPIs — In-Memory Excel Processing (No DB)
# ─────────────────────────────────────────────────────────

class FilterOptionsView(APIView):
    """
    GET /api/kpis/filter-options/

    Returns distinct filter choices for week, team, style, color, customer, batch
    from the QualityQcFa table. Used to populate dynamic filter selects/datalists.

    Supports context parameter:
        - ?context=plant → filter by table_type='QFA' (default)
        - ?context=customer → filter by table_type='QFC'
    """

    def get(self, request):
        # Resolve context parameter → table_type filter
        try:
            table_type = _resolve_context_table_type(request.query_params.get('context'))
        except rest_framework_exceptions.ValidationError as e:
            return Response(e.detail, status=http_status.HTTP_400_BAD_REQUEST)

        base_qs = QualityQcFa.objects.filter(table_type=table_type)

        weeks = list(
            base_qs.values_list('week', flat=True)
            .distinct()
            .order_by('week')
        )
        teams = list(
            base_qs.values_list('team', flat=True)
            .distinct()
            .order_by('team')
        )
        # Only expose valid 1..36 teams in filter options
        teams = [t for t in teams if t is not None and 1 <= t <= 36]
        styles = list(
            base_qs.values_list('style', flat=True)
            .distinct()
            .order_by('style')
        )
        colors = list(
            Color.objects.filter(is_active=True)
            .values_list('name', flat=True)
            .distinct()
            .order_by('name')
        )
        customers = list(
            base_qs.values_list('customer', flat=True)
            .distinct()
            .order_by('customer')
        )
        batches = list(
            base_qs.values_list('batch', flat=True)
            .distinct()
            .order_by('batch')
        )

        # Dual-line filter options: distinct non-null line_code values
        line_codes = list(
            base_qs.filter(line_code__isnull=False)
            .values_list('line_code', flat=True)
            .distinct()
            .order_by('line_code')
        )
        include_dual_lines_default = len(line_codes) > 0

        payload = {
            'week': [w for w in weeks if w is not None],
            'team': [t for t in teams if t is not None],
            'line_code': [lc for lc in line_codes if lc is not None],
            'style': [s for s in styles if s is not None],
            'color': [c for c in colors if c is not None],
            'customer': [c for c in customers if c is not None],
            'batch': [b for b in batches if b is not None],
            'include_dual_lines_default': include_dual_lines_default,
        }

        dto_data = _serialize_payload(FilterOptionsSerializer, payload, many=False)
        return Response(dto_data)


class VolatileKpiView(APIView):
    """
    POST /api/kpis/volatile/

    Recibe un archivo Excel via FormData, lo procesa en memoria (sin guardar
    en la base de datos) y devuelve 16 KPIs en el mismo formato que los
    endpoints live.

    Solo usa el sheet "QC FA Plant". Los KPIs que requieren datos de otras
    tablas (SecondsA4, InspectionDefect, Container) se devuelven como null.
    """
    parser_classes = [MultiPartParser]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=400)

        try:
            # Parsear QC FA Plant (header=2, 67 columnas)
            df = load_and_clean(
                file_obj,
                QC_FA_PLANT_REMAP,
                QC_FA_PLANT_NUMERIC_COLUMNS,
                QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
                "QC FA Plant",
                2,
                67,
            )
            rows = df.to_dict('records')

            # Parsear KPIs desde ranges dinámicos del Excel
            try:
                seconds_rework = parse_seconds_rework(file_obj)
            except Exception:
                seconds_rework = None

            try:
                fabric_defects = parse_fabric_defects(file_obj)
            except Exception:
                fabric_defects = None

            try:
                containers = parse_containers_by_state(file_obj)
            except Exception:
                containers = None

            # Calcular los 14 KPIs usando DTO serializers para mantener frontera explícita
            kpis = {
                "aql_by_style": _serialize_payload(KpiBarSerializer, self._calc_aql_by_style(rows), many=True),
                "aql_weekly": _serialize_payload(KpiSeriesSerializer, self._calc_aql_weekly(rows), many=True),
                "audited_pieces": _serialize_payload(KpiSeriesSerializer, self._calc_audited_pieces(rows), many=True),
                "ac_re_rate_by_line": _serialize_payload(KpiBarSerializer, self._calc_ac_re_rate(rows), many=True),
                "seconds_rework": _serialize_payload(KpiSeriesSerializer, seconds_rework, many=True) if seconds_rework is not None else None,
                "performance_by_customer": _serialize_payload(KpiBarSerializer, self._calc_perf_by_customer(rows), many=True),
                "performance_by_line": _serialize_payload(KpiBarSerializer, self._calc_perf_by_line(rows), many=True),
                "top_defects": _serialize_payload(KpiBarSerializer, parse_top_defects(rows), many=True),
                "fabric_defects": _serialize_payload(KpiBarSerializer, fabric_defects, many=True) if fabric_defects is not None else None,
                "defects_by_style_type": _serialize_payload(KpiHeatmapSerializer, parse_defects_by_style(rows), many=True),
                "pass_reject_distribution": _serialize_payload(KpiDonutSerializer, self._calc_pass_reject(rows), many=True),
                "rejected_evolution": _serialize_payload(KpiSeriesSerializer, self._calc_rejected_evolution(rows), many=True),
                "containers_by_state": _serialize_payload(KpiDonutSerializer, containers, many=True) if containers is not None else None,
                "defect_rate": _serialize_payload(ScalarMetricSerializer, self._calc_defect_rate(rows), many=False),
                "defect_composition": _serialize_payload(KpiDonutSerializer, self._calc_defect_composition(rows), many=True),
                "defect_trend_top_3": _serialize_payload(KpiSeriesSerializer, self._calc_defect_trend_top_3(rows), many=True),
            }

            filter_options = self._compute_filter_options(rows)
            kpis["filter_options"] = _serialize_payload(FilterOptionsSerializer, filter_options, many=False)

            return Response(kpis, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def _calc_aql_by_style(self, rows):
        """GROUP BY style: SUM(defects_total)/SUM(sample)*100"""
        df = pd.DataFrame(rows)
        if df.empty:
            return []
        grouped = df.groupby('style').agg(
            total_defects=('defects_total', 'sum'),
            total_sample=('sample', 'sum')
        ).reset_index()
        grouped = grouped[grouped['total_sample'] > 0]
        grouped['aql'] = (grouped['total_defects'] / grouped['total_sample'] * 100).round(2)
        result = [
            {"label": row['style'], "value": row['aql']}
            for _, row in grouped.iterrows()
        ]
        result.sort(key=lambda x: x['value'], reverse=True)
        return result

    def _calc_aql_weekly(self, rows):
        """GROUP BY week: SUM(defects_total)/SUM(sample)*100 con línea de tendencia."""
        df = pd.DataFrame(rows)
        if df.empty:
            return [{"name": "AQL", "data": []}, {"name": "Trend", "data": []}]

        grouped = df.groupby('week').agg(
            total_defects=('defects_total', 'sum'),
            total_sample=('sample', 'sum')
        ).reset_index().sort_values('week')

        aql_data = []
        for _, row in grouped.iterrows():
            sample = row['total_sample'] or 0
            defects = row['total_defects'] or 0
            aql = (defects / sample * 100) if sample > 0 else 0.0
            aql_data.append({"x": int(row['week']), "y": round(aql, 2)})

        # Calcular línea de tendencia
        trend_data = []
        if len(aql_data) >= 2:
            differences = []
            for i in range(1, len(aql_data)):
                diff = aql_data[i]['y'] - aql_data[i - 1]['y']
                differences.append(diff)
            slope = sum(differences) / len(differences) if differences else 0
            first_x = aql_data[0]['x']
            first_y = aql_data[0]['y']
            for point in aql_data:
                trend_y = first_y + slope * (point['x'] - first_x)
                trend_data.append({"x": point['x'], "y": round(trend_y, 2)})
        elif len(aql_data) == 1:
            trend_data = [{"x": aql_data[0]['x'], "y": aql_data[0]['y']}]

        return [{"name": "AQL", "data": aql_data}, {"name": "Trend", "data": trend_data}]

    def _calc_audited_pieces(self, rows):
        """GROUP BY week: SUM(sample)"""
        df = pd.DataFrame(rows)
        if df.empty:
            return [{"name": "Pieces", "data": []}]

        grouped = df.groupby('week').agg(
            total_sample=('sample', 'sum')
        ).reset_index().sort_values('week')

        pieces_data = [
            {"x": int(row['week']), "y": int(row['total_sample'] or 0)}
            for _, row in grouped.iterrows()
        ]
        return [{"name": "Pieces", "data": pieces_data}]

    def _calc_ac_re_rate(self, rows):
        """GROUP BY team × pass_or_fail: COUNT de registros.
        Teams are canonicalized (60→6) and filtered to 1..36."""
        df = pd.DataFrame(rows)
        if df.empty:
            return []

        # Sanitize: canonicalize 60→6, exclude teams outside 1..36
        df = _sanitize_team_dataframe(df)
        if df.empty:
            return []

        df = df.dropna(subset=['pass_or_fail'])

        grouped = df.groupby(['team', 'pass_or_fail']).size().reset_index(name='count')

        result = [
            {"label": f"{int(row['team'])} - {row['pass_or_fail']}", "value": int(row['count'])}
            for _, row in grouped.iterrows()
        ]
        return result

    def _calc_perf_by_customer(self, rows):
        """GROUP BY customer: accepted / (accepted + rejected) * 100"""
        df = pd.DataFrame(rows)
        if df.empty:
            return []

        grouped = df.groupby('customer').agg(
            total_accepted=('accepted', 'sum'),
            total_rejected=('rejected', 'sum'),
        ).reset_index()

        result = [
            {
                "label": row['customer'],
                "value": _calculate_acceptance_rate(
                    row['total_accepted'], row['total_rejected']
                ),
            }
            for _, row in grouped.iterrows()
        ]
        return result

    def _calc_perf_by_line(self, rows):
        """GROUP BY team: accepted / (accepted + rejected) * 100.
        Teams outside 1..36 are excluded (metric-scoped sanitization)."""
        df = pd.DataFrame(rows)
        if df.empty:
            return []

        # Sanitize: exclude teams outside valid range 1..36
        df = _sanitize_team_dataframe(df)

        if df.empty:
            return []

        grouped = df.groupby('team').agg(
            total_accepted=('accepted', 'sum'),
            total_rejected=('rejected', 'sum'),
        ).reset_index()

        result = [
            {
                "label": str(int(row['team'])),
                "value": _calculate_acceptance_rate(
                    row['total_accepted'], row['total_rejected']
                ),
            }
            for _, row in grouped.iterrows()
        ]
        return result

    def _calc_pass_reject(self, rows):
        """GROUP BY pass_or_fail: COUNT"""
        df = pd.DataFrame(rows)
        if df.empty:
            return []

        grouped = df.groupby('pass_or_fail').size().reset_index(name='value')
        result = [
            {"name": row['pass_or_fail'], "value": int(row['value'])}
            for _, row in grouped.iterrows()
        ]
        return result

    def _calc_rejected_evolution(self, rows):
        """GROUP BY week: SUM(rejected)"""
        df = pd.DataFrame(rows)
        if df.empty:
            return [{"name": "Rejected", "data": []}]

        grouped = df.groupby('week').agg(
            total_rejected=('rejected', 'sum')
        ).reset_index().sort_values('week')

        rejected_data = [
            {"x": int(row['week']), "y": int(row['total_rejected'] or 0)}
            for _, row in grouped.iterrows()
        ]
        return [{"name": "Rejected", "data": rejected_data}]

    def _calc_defect_rate(self, rows):
        """SUM(defects_total)/SUM(sample)*100 global"""
        df = pd.DataFrame(rows)
        if df.empty:
            return {"label": "Defect Rate", "value": 0}

        total_defects = df['defects_total'].sum()
        total_sample = df['sample'].sum()

        value = 0
        if total_sample > 0:
            value = round((total_defects / total_sample) * 100, 2)

        return {"label": "Defect Rate", "value": value}

    def _compute_filter_options(self, rows):
        """
        Compute distinct filter options from parsed Excel rows.
        Returns { week, team, style, color, customer, batch }.
        """
        df = pd.DataFrame(rows)
        if df.empty:
            return {
                'week': [],
                'team': [],
                'style': [],
                'color': [],
                'customer': [],
                'batch': [],
            }

        options = {}
        for field in ['week', 'team', 'style', 'customer', 'batch']:
            if field in df.columns:
                distinct = df[field].dropna().unique().tolist()
                if field in ('week', 'team', 'batch'):
                    import numpy as np
                    numeric_distinct = pd.to_numeric(pd.Series(distinct), errors='coerce')
                    integer_values = numeric_distinct[numeric_distinct.notna() & np.isfinite(numeric_distinct)]
                    values = sorted({int(value) for value in integer_values.tolist() if float(value).is_integer()})
                    if field == 'team':
                        values = [v for v in values if 1 <= v <= 36]
                    options[field] = values
                else:
                    options[field] = sorted([str(x) for x in distinct])
            else:
                options[field] = []

        if 'color__name' in df.columns:
            options['color'] = sorted([str(x) for x in df['color__name'].dropna().unique().tolist()])
        elif 'color' in df.columns:
            options['color'] = sorted([str(x) for x in df['color'].dropna().unique().tolist()])
        else:
            options['color'] = []

        return options

    def _calc_defect_composition(self, rows):
        """
        Compute defect composition from parsed QC rows (volatile mode).

        Sums each defect column across all rows, maps field names to human
        labels via DEFECT_LABEL_MAP, excludes zero totals, and sorts by
        value DESC, name ASC.

        Returns: [{name: str, value: int}] — same shape as live endpoint.
        """
        if not rows:
            return []

        totals = {}
        for field in QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS:
            total = sum(int(row.get(field, 0) or 0) for row in rows)
            if total > 0:
                label = DEFECT_LABEL_MAP.get(field, field.replace('_', ' ').title())
                totals[label] = totals.get(label, 0) + total

        result = [{"name": k, "value": v} for k, v in totals.items()]
        result.sort(key=lambda x: (-x["value"], x["name"]))
        return result

    def _calc_defect_trend_top_3(self, rows):
        """
        Compute top-3 defect weekly trend from parsed QC rows (volatile mode).

        Steps:
          1. Sum each defect column across ALL rows to find top 3 by total.
          2. Group by (week, defect field) for weekly totals.
          3. Build dense series — every filtered week present, y=0 for absent.
        Returns: [{name: str, data: [{x: int, y: int}]}] — up to 3 series.
        Returns [] when no positive defect amounts.
        """
        if not rows:
            return []

        # Step 1: Global totals per defect field
        global_totals = {}
        for field in QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS:
            total = sum(int(row.get(field, 0) or 0) for row in rows)
            if total > 0:
                label = DEFECT_LABEL_MAP.get(field, field.replace('_', ' ').title())
                global_totals[label] = global_totals.get(label, 0) + total

        if not global_totals:
            return []

        # Top 3 by total, tie-break by name ASC
        top_defects = sorted(
            global_totals.items(),
            key=lambda x: (-x[1], x[0]),
        )[:3]
        top_names = [name for name, _ in top_defects]

        # Step 2: Weekly aggregation
        # Collect weeks
        weeks_set = set()
        weekly_data = {}  # {defect_label: {week: amount}}
        for row in rows:
            week = int(row.get('week', 0) or 0)
            weeks_set.add(week)
            for field in QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS:
                label = DEFECT_LABEL_MAP.get(field, field.replace('_', ' ').title())
                if label not in top_names:
                    continue
                amount = int(row.get(field, 0) or 0)
                if label not in weekly_data:
                    weekly_data[label] = {}
                weekly_data[label][week] = weekly_data[label].get(week, 0) + amount

        filtered_weeks = sorted(weeks_set)

        # Step 3: Build dense series
        result = []
        for name in top_names:
            data = [
                {"x": week, "y": weekly_data.get(name, {}).get(week, 0)}
                for week in filtered_weeks
            ]
            result.append({"name": name, "data": data})

        return result

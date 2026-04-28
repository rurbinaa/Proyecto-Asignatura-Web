from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework import exceptions as rest_framework_exceptions
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Count, Case, When, F
import pandas as pd
import numpy as np
import datetime
from quality_data.models import QualityQcFa, SecondsA4, SecondsGeneral, Container, ExcelSyncSession, InspectionDefect, Color
from excel_importer.handler_service import (
    load_and_clean,
    bulk_insert,
    bulk_insert_seconds_a4,
    bulk_insert_seconds_general,
    bulk_insert_container,
)
from excel_importer.sheet_configs import (
    SHEET_NAMES,
    QC_FA_PLANT_REMAP,
    QC_FA_PLANT_NUMERIC_COLUMNS,
    QC_FA_PLANT_NOT_NUMERIC_COLUMNS,
    QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
    QC_FA_CUSTOMER_REMAP,
    QC_FA_CUSTOMER_NUMERIC_COLUMNS,
    QC_FA_CUSTOMER_NOT_NUMERIC_COLUMNS,
    QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
    SECONDS_A4_REMAP,
    SECONDS_A4_NUMERIC_COLUMNS,
    SECONDS_A4_NOT_NUMERIC_COLUMNS,
    SECONDS_GENERAL_REMAP,
    SECONDS_GENERAL_NUMERIC_COLUMNS,
    SECONDS_GENERAL_NOT_NUMERIC_COLUMNS,
    CONTAINER_REMAP,
    CONTAINER_NUMERIC_COLUMNS,
    CONTAINER_NOT_NUMERIC_COLUMNS,
    CONTAINER_AMOUNT_DEFEACTS_FIELDS
)
from excel_importer.sync_service import (
    create_session_from_dataframes,
    apply_session,
    reject_session,
)
from excel_importer.pivot_parsers import (
    parse_seconds_rework,
    parse_cut_qty,
    parse_fabric_defects,
    parse_enganche,
    parse_top_defects,
    parse_defects_by_style,
    parse_containers_by_state,
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
    KpiDonutEnvelopeSerializer,
    KpiHeatmapEnvelopeSerializer,
    ScalarMetricSerializer,
    FilterOptionsSerializer,
)

def _get_incremental_rows(df, model_class, **filters):
    db_rows = model_class.objects.filter(**filters).count()
    df_rows = len(df)
    rows_to_insert = max(df_rows - db_rows, 0)

    if rows_to_insert == 0:
        return df.iloc[0:0]

    return df.tail(rows_to_insert).copy()


def _df_to_json_safe(df):
    """
    Convert a DataFrame to a list of dicts with JSON-serializable values.

    Handles:
    - pandas.Timestamp / datetime → ISO date string (YYYY-MM-DD)
    - numpy.integer / numpy.floating → Python int / float
    - numpy.bool_ → Python bool
    - pandas.NaT / None → None
    """
    if df is None or df.empty:
        return []

    records = df.to_dict('records')
    result = []
    for row in records:
        clean_row = {}
        for key, value in row.items():
            if value is None or pd.isna(value):
                clean_row[key] = None
            elif isinstance(value, (pd.Timestamp, datetime.datetime)):
                clean_row[key] = value.strftime("%Y-%m-%d")
            elif isinstance(value, datetime.date):
                clean_row[key] = value.strftime("%Y-%m-%d")
            elif isinstance(value, (np.integer,)):
                clean_row[key] = int(value)
            elif isinstance(value, (np.floating,)):
                clean_row[key] = float(value)
            elif isinstance(value, (np.bool_,)):
                clean_row[key] = bool(value)
            elif isinstance(value, np.ndarray):
                clean_row[key] = value.tolist()
            else:
                clean_row[key] = value
        result.append(clean_row)
    return result


def _serialize_payload(serializer_cls, payload, many=False):
    """Serialize a payload using a DTO serializer class."""
    serializer = serializer_cls(payload, many=many)
    return serializer.data


def _serialize_envelope(envelope_serializer_cls, payload):
    """Serialize a `{data: [...]}` response using an envelope serializer class."""
    serializer = envelope_serializer_cls({"data": payload})
    return serializer.data

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
        _qc_fa_plant_df = load_and_clean(
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
            None,
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


# DEPRECATED: Use ExcelPreviewView + ExcelConfirmView instead.
# Kept for backward compatibility. Will be removed in a future version.
class SaveData(APIView):
    parser_classes = [MultiPartParser]

    def post (self, request, filename, format = None):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=400)

        qc_fa_plant_df = load_and_clean(
            file_obj,
            QC_FA_PLANT_REMAP,
            QC_FA_PLANT_NUMERIC_COLUMNS,
            QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
            *SHEET_NAMES[0],
        )
        qc_fa_customer_df = load_and_clean(
            file_obj,
            QC_FA_CUSTOMER_REMAP,
            QC_FA_CUSTOMER_NUMERIC_COLUMNS,
            QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
            *SHEET_NAMES[1],
        )

        seconds_a4_df = load_and_clean(
            file_obj,
            SECONDS_A4_REMAP,
            SECONDS_A4_NUMERIC_COLUMNS,
            None,
            *SHEET_NAMES[2],
        )

        seconds_general_df = load_and_clean(
            file_obj,
            SECONDS_GENERAL_REMAP,
            SECONDS_GENERAL_NUMERIC_COLUMNS,
            None,
            *SHEET_NAMES[3],
        )

        container_df = load_and_clean(
            file_obj,
            CONTAINER_REMAP,
            CONTAINER_NUMERIC_COLUMNS,
            CONTAINER_AMOUNT_DEFEACTS_FIELDS,
            *SHEET_NAMES[4],
        )

        qc_fa_plant_new_rows = _get_incremental_rows(qc_fa_plant_df, QualityQcFa, table_type="QFA")
        bulk_insert(
            qc_fa_plant_new_rows,
            QC_FA_PLANT_NUMERIC_COLUMNS,
            QC_FA_PLANT_NOT_NUMERIC_COLUMNS,
            QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
            table_type="QFA",
        )

        qc_fa_customer_new_rows = _get_incremental_rows(qc_fa_customer_df, QualityQcFa, table_type="QFC")
        bulk_insert(
            qc_fa_customer_new_rows,
            QC_FA_CUSTOMER_NUMERIC_COLUMNS,
            QC_FA_CUSTOMER_NOT_NUMERIC_COLUMNS,
            QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
            table_type="QFC",
        )

        seconds_a4_new_rows = _get_incremental_rows(seconds_a4_df, SecondsA4)
        seconds_general_new_rows = _get_incremental_rows(seconds_general_df, SecondsGeneral)
        container_new_rows = _get_incremental_rows(container_df, Container)

        bulk_insert_seconds_a4(
            seconds_a4_new_rows,
            SECONDS_A4_NUMERIC_COLUMNS,
            SECONDS_A4_NOT_NUMERIC_COLUMNS,
        )

        bulk_insert_seconds_general(
            seconds_general_new_rows,
            SECONDS_GENERAL_NUMERIC_COLUMNS,
            SECONDS_GENERAL_NOT_NUMERIC_COLUMNS,
        )

        bulk_insert_container(
            container_new_rows,
            CONTAINER_NUMERIC_COLUMNS,
            CONTAINER_NOT_NUMERIC_COLUMNS,
            CONTAINER_AMOUNT_DEFEACTS_FIELDS,
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
            import pandas as pd

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
                None, *SHEET_NAMES[3],
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

        return queryset


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

        return Response(result, status=http_status.HTTP_200_OK)


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
        from django.db.models import Sum

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

        return Response(result, status=http_status.HTTP_200_OK)


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

        return Response(result, status=http_status.HTTP_200_OK)


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

        return Response(result, status=http_status.HTTP_200_OK)


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

        return Response(result, status=http_status.HTTP_200_OK)


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

        return Response(result, status=http_status.HTTP_200_OK)

class DefectRateView(KpiFilterMixin, APIView):
    """
    GET /api/kpis/defect-rate/

    Source: QualityQcFa
    Global average: SUM(defects_total) / SUM(sample) * 100

    Response: {"label": "Defect Rate", "value": 2.34}
    If total sample = 0 → value = 0
    """

    def get(self, request):
        queryset = self.get_filtered_queryset(QualityQcFa.objects.all())

        aggregated = queryset.aggregate(
            total_defects=Sum('defects_total'),
            total_sample=Sum('sample'),
        )

        total_defects = aggregated['total_defects'] or 0
        total_sample = aggregated['total_sample'] or 0

        value = 0
        if total_sample > 0:
            value = round((total_defects / total_sample) * 100, 2)

        result = {"label": "Defect Rate", "value": value}

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
        GROUP BY team × pass_or_fail: COUNT of records.

        Response: [{"label": "Line 1 - PASS", "value": 45}, {"label": "Line 1 - REJECT", "value": 5}, ...]
        """
        queryset = self.get_quality_queryset()

        aggregated = (
            queryset
            .values(team_name=F('team'), pof=F('pass_or_fail'))
            .annotate(count=Count('id'))
            .order_by('team_name', 'pof')
        )

        result = [
            {"label": f"{item['team_name']} - {item['pof']}", "value": item['count']}
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
        GROUP BY customer: SUM(accepted) / SUM(sample) * 100.
        Filter where sample > 0.

        Response: [{"label": "Customer X", "value": 92.5}, ...]
        """
        queryset = self.get_quality_queryset().filter(sample__gt=0)

        aggregated = (
            queryset
            .values(customer_name=F('customer'))
            .annotate(
                total_accepted=Sum('accepted'),
                total_sample=Sum('sample'),
            )
            .order_by('customer_name')
        )

        result = [
            {
                "label": item['customer_name'],
                "value": round((item['total_accepted'] / item['total_sample']) * 100, 2)
                if item['total_sample'] > 0 else 0,
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
        GROUP BY team: SUM(accepted) / SUM(sample) * 100.

        Response: [{"label": "Line 1", "value": 95.2}, ...]
        """
        queryset = self.get_quality_queryset()

        aggregated = (
            queryset
            .values(team_name=F('team'))
            .annotate(
                total_accepted=Sum('accepted'),
                total_sample=Sum('sample'),
            )
            .order_by('team_name')
        )

        result = [
            {
                "label": f"{item['team_name']}",
                "value": round((item['total_accepted'] / item['total_sample']) * 100, 2)
                if item['total_sample'] > 0 else 0,
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

    @action(detail=False, methods=['get'], url_path='aql-by-style')
    def aql_by_style(self, request):
        """
        GET /api/kpis/aql-by-style/

        Returns AQL percentage grouped by style.
        Formula: SUM(defects_total) / SUM(sample) * 100
        """
        queryset = self.get_filtered_queryset(self.get_queryset())

        if not queryset.exists():
            return Response(_serialize_envelope(KpiBarEnvelopeSerializer, []))

        # GROUP BY style: SUM(defects_total) / SUM(sample) * 100
        annotated = (
            queryset
            .values('style')
            .annotate(
                total_defects=Sum('defects_total'),
                total_sample=Sum('sample'),
            )
        )

        result = []
        for row in annotated:
            sample = row['total_sample'] or 0
            defects = row['total_defects'] or 0
            if sample > 0:
                aql = (defects / sample) * 100
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
        Formula: SUM(defects_total) / SUM(sample) * 100
        """
        queryset = self.get_filtered_queryset(self.get_queryset())

        if not queryset.exists():
            return Response(_serialize_envelope(KpiSeriesEnvelopeSerializer, []))

        # GROUP BY week: SUM(defects_total) / SUM(sample) * 100
        annotated = (
            queryset
            .values('week')
            .annotate(
                total_defects=Sum('defects_total'),
                total_sample=Sum('sample'),
            )
            .order_by('week')
        )

        # Build series data
        aql_data = []
        for row in annotated:
            week = row['week']
            total_defects = row['total_defects'] or 0
            total_sample = row['total_sample'] or 0
            aql = (total_defects / total_sample * 100) if total_sample > 0 else 0.0
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
    """

    def get(self, request):
        weeks = list(
            QualityQcFa.objects.values_list('week', flat=True)
            .distinct()
            .order_by('week')
        )
        teams = list(
            QualityQcFa.objects.values_list('team', flat=True)
            .distinct()
            .order_by('team')
        )
        styles = list(
            QualityQcFa.objects.values_list('style', flat=True)
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
            QualityQcFa.objects.values_list('customer', flat=True)
            .distinct()
            .order_by('customer')
        )
        batches = list(
            QualityQcFa.objects.values_list('batch', flat=True)
            .distinct()
            .order_by('batch')
        )

        return Response({
            'week': [w for w in weeks if w is not None],
            'team': [t for t in teams if t is not None],
            'style': [s for s in styles if s is not None],
            'color': [c for c in colors if c is not None],
            'customer': [c for c in customers if c is not None],
            'batch': [b for b in batches if b is not None],
        })


class VolatileKpiView(APIView):
    """
    POST /api/kpis/volatile/

    Recibe un archivo Excel via FormData, lo procesa en memoria (sin guardar
    en la base de datos) y devuelve los 14 KPIs en el mismo formato que los
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

            # Calcular los 14 KPIs usando pandas
            kpis = {
                "aql_by_style": self._calc_aql_by_style(rows),
                "aql_weekly": self._calc_aql_weekly(rows),
                "audited_pieces": self._calc_audited_pieces(rows),
                "ac_re_rate_by_line": self._calc_ac_re_rate(rows),
                "seconds_rework": seconds_rework,
                "performance_by_customer": self._calc_perf_by_customer(rows),
                "performance_by_line": self._calc_perf_by_line(rows),
                "top_defects": parse_top_defects(rows),
                "fabric_defects": fabric_defects,
                "defects_by_style_type": parse_defects_by_style(rows),
                "pass_reject_distribution": self._calc_pass_reject(rows),
                "rejected_evolution": self._calc_rejected_evolution(rows),
                "containers_by_state": containers,
                "defect_rate": self._calc_defect_rate(rows),
            }

            filter_options = self._compute_filter_options(rows)
            kpis["filter_options"] = filter_options

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
        """GROUP BY team × pass_or_fail: COUNT de registros."""
        df = pd.DataFrame(rows)
        if df.empty:
            return []

        # Filtrar filas válidas con team y pass_or_fail
        df = df.dropna(subset=['team', 'pass_or_fail'])
        df = df[df['team'] != 0]

        grouped = df.groupby(['team', 'pass_or_fail']).size().reset_index(name='count')

        result = [
            {"label": f"{int(row['team'])} - {row['pass_or_fail']}", "value": int(row['count'])}
            for _, row in grouped.iterrows()
        ]
        return result

    def _calc_perf_by_customer(self, rows):
        """GROUP BY customer: SUM(accepted)/SUM(sample)*100"""
        df = pd.DataFrame(rows)
        if df.empty:
            return []

        df = df[df['sample'] > 0]
        grouped = df.groupby('customer').agg(
            total_accepted=('accepted', 'sum'),
            total_sample=('sample', 'sum')
        ).reset_index()

        result = [
            {
                "label": row['customer'],
                "value": round((row['total_accepted'] / row['total_sample']) * 100, 2)
                if row['total_sample'] > 0 else 0,
            }
            for _, row in grouped.iterrows()
        ]
        return result

    def _calc_perf_by_line(self, rows):
        """GROUP BY team: SUM(accepted)/SUM(sample)*100"""
        df = pd.DataFrame(rows)
        if df.empty:
            return []

        grouped = df.groupby('team').agg(
            total_accepted=('accepted', 'sum'),
            total_sample=('sample', 'sum')
        ).reset_index()

        result = [
            {
                "label": str(int(row['team'])),
                "value": round((row['total_accepted'] / row['total_sample']) * 100, 2)
                if row['total_sample'] > 0 else 0,
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
                    options[field] = sorted({int(value) for value in integer_values.tolist() if float(value).is_integer()})
                else:
                    options[field] = sorted([str(x) for x in distinct])
            else:
                options[field] = []

        if 'color__name' in df.columns:
            options['color'] = sorted(df['color__name'].dropna().unique().tolist())
        elif 'color' in df.columns:
            options['color'] = sorted(df['color'].dropna().unique().tolist())
        else:
            options['color'] = []

        return options

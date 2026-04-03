from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Avg, Count, FloatField, ExpressionWrapper, Case, When, Value, F
import pandas as pd
import numpy as np
import datetime
from quality_data.models import QualityQcFa, SecondsA4, SecondsGeneral, Container, ExcelSyncSession, InspectionDefect, DefectType
from quality_data.serializers import KpiBarSerializer
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

class Process(APIView):
    """
    Process an uploaded Excel file for preview (V2 workflow).

    Note: This endpoint only uses qc_fa_plant_df for parsing validation.
    The other 4 sheets are parsed but discarded because the real sync
    happens in ExcelConfirmView after user confirmation.

    This endpoint exists to support the upload → preview → confirm workflow.
    """
    parser_classes = [FileUploadParser]

    def post (self, request, filename, format = None):
        file_obj = request.data['file']

        # Only qc_fa_plant_df is used for validation in this endpoint.
        # The other sheets are parsed but not used here - they will be
        # processed in ExcelConfirmView after user confirms the preview.
        qc_fa_plant_df = load_and_clean(
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
    parser_classes = [FileUploadParser]

    def post (self, request, filename, format = None):
        file_obj = request.data['file']

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
    parser_classes = [FileUploadParser]

    def post(self, request, filename, format=None):
        file_obj = request.data['file']

        try:
            # Parse all 5 sheets
            dataframes = {}

            qc_fa_plant_df = load_and_clean(
                file_obj, QC_FA_PLANT_REMAP, QC_FA_PLANT_NUMERIC_COLUMNS,
                QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS, *SHEET_NAMES[0],
            )
            dataframes["qc_fa_plant"] = _df_to_json_safe(qc_fa_plant_df)

            qc_fa_customer_df = load_and_clean(
                file_obj, QC_FA_CUSTOMER_REMAP, QC_FA_CUSTOMER_NUMERIC_COLUMNS,
                QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS, *SHEET_NAMES[1],
            )
            dataframes["qc_fa_customer"] = _df_to_json_safe(qc_fa_customer_df)

            seconds_a4_df = load_and_clean(
                file_obj, SECONDS_A4_REMAP, SECONDS_A4_NUMERIC_COLUMNS,
                None, *SHEET_NAMES[2],
            )
            dataframes["seconds_a4"] = _df_to_json_safe(seconds_a4_df)

            seconds_general_df = load_and_clean(
                file_obj, SECONDS_GENERAL_REMAP, SECONDS_GENERAL_NUMERIC_COLUMNS,
                None, *SHEET_NAMES[3],
            )
            dataframes["seconds_general"] = _df_to_json_safe(seconds_general_df)

            container_df = load_and_clean(
                file_obj, CONTAINER_REMAP, CONTAINER_NUMERIC_COLUMNS,
                CONTAINER_AMOUNT_DEFEACTS_FIELDS, *SHEET_NAMES[4],
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
        - style: style__icontains
        - color: color__name__icontains
        - customer: customer__icontains
        - batch: batch__exact
    """

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

        # date_range: "start_date,end_date" → date_1__gte, date_1__lte
        date_range = request.query_params.get('date_range')
        if date_range:
            parts = date_range.split(',')
            if len(parts) == 2:
                start_date, end_date = parts[0].strip(), parts[1].strip()
                if start_date:
                    filters['date_1__gte'] = start_date
                if end_date:
                    filters['date_1__lte'] = end_date

        # week: exact integer match
        week = request.query_params.get('week')
        if week:
            filters['week__exact'] = int(week)

        # team: exact integer match
        team = request.query_params.get('team')
        if team:
            filters['team__exact'] = int(team)

        # style: case-insensitive contains
        style = request.query_params.get('style')
        if style:
            filters['style__icontains'] = style

        # color: foreign key lookup via color__name (case-insensitive contains)
        color = request.query_params.get('color')
        if color:
            filters['color__name__icontains'] = color

        # customer: case-insensitive contains
        customer = request.query_params.get('customer')
        if customer:
            filters['customer__icontains'] = customer

        # batch: exact integer match
        batch = request.query_params.get('batch')
        if batch:
            filters['batch__exact'] = int(batch)

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


class FabricDefectsView(APIView):
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
        queryset = SecondsGeneral.objects.all()

        # Apply date filters if provided
        date_range = request.query_params.get('date_range')
        if date_range:
            parts = date_range.split(',')
            if len(parts) == 2:
                start_date, end_date = parts[0].strip(), parts[1].strip()
                if start_date:
                    queryset = queryset.filter(date__gte=start_date)
                if end_date:
                    queryset = queryset.filter(date__lte=end_date)

        week = request.query_params.get('week')
        if week:
            queryset = queryset.filter(week__exact=int(week))

        # Aggregate each fabric defect column
        aggregated = queryset.aggregate(
            corrido=Sum('corrido_2'),
            barre=Sum('barre'),
            otros=Sum('otros_3'),
            degradacion=Sum('degradacion'),
            bordados=Sum('bordados'),
        )

        result = [
            {"label": "Corrido", "value": aggregated['corrido'] or 0},
            {"label": "Barre", "value": aggregated['barre'] or 0},
            {"label": "Otros", "value": aggregated['otros'] or 0},
            {"label": "Degradación", "value": aggregated['degradacion'] or 0},
            {"label": "Bordados", "value": aggregated['bordados'] or 0},
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
        # Get top 5 styles by total defect amount
        top_styles = (
            InspectionDefect.objects
            .values(style_name=F('inspection__style'))
            .annotate(total=Sum('amount'))
            .order_by('-total')[:5]
        )
        top_style_names = [item['style_name'] for item in top_styles]

        # Get top 5 defect types by total amount
        top_defect_types = (
            InspectionDefect.objects
            .values(defect_type_name=F('defect_type__name'))
            .annotate(total=Sum('amount'))
            .order_by('-total')[:5]
        )
        top_defect_type_names = [item['defect_type_name'] for item in top_defect_types]

        # Get filtered queryset and filter by top styles and defect types
        queryset = InspectionDefect.objects.filter(
            inspection__style__in=top_style_names,
            defect_type__name__in=top_defect_type_names,
        )
        queryset = self.get_filtered_queryset(queryset)

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
            .values(pass_or_fail=F('pass_or_fail'))
            .annotate(count=Count('id'))
            .order_by('pass_or_fail')
        )

        result = [
            {"name": item['pass_or_fail'], "value": item['count']}
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
            .values(week=F('week'))
            .annotate(total_rejected=Sum('rejected'))
            .order_by('week')
        )

        result = [{
            "name": "Rejected",
            "data": [
                {"x": item['week'], "y": item['total_rejected'] or 0}
                for item in aggregated
            ]
        }]

        return Response(result, status=http_status.HTTP_200_OK)


class ContainersByStateView(APIView):
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
            queryset = queryset.filter(customer__icontains=customer)

        # Use Case/When for range grouping
        from django.db.models import Case, When, IntegerField

        aggregated = (
            queryset
            .annotate(
                range_bucket=Case(
                    When(percentage_pass__lt=80, then=1),
                    When(percentage_pass__gte=80, percentage_pass__lt=90, then=2),
                    When(percentage_pass__gte=90, percentage_pass__lt=95, then=3),
                    When(percentage_pass__gte=95, then=4),
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
            .values(team=F('team'), pass_or_fail=F('pass_or_fail'))
            .annotate(count=Count('id'))
            .order_by('team', 'pass_or_fail')
        )

        result = [
            {"label": f"{item['team']} - {item['pass_or_fail']}", "value": item['count']}
            for item in aggregated
        ]

        return Response(result, status=http_status.HTTP_200_OK)

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

        # Apply date filters if provided
        date_range = request.query_params.get('date_range')
        if date_range:
            parts = date_range.split(',')
            if len(parts) == 2:
                start_date, end_date = parts[0].strip(), parts[1].strip()
                if start_date:
                    queryset = queryset.filter(date__gte=start_date)
                if end_date:
                    queryset = queryset.filter(date__lte=end_date)

        aggregated = (
            queryset
            .values(week=F('week'))
            .annotate(
                total_sew=Sum('seconds_by_sew'),
                total_fab=Sum('seconds_by_fab'),
            )
            .order_by('week')
        )

        sewing_data = [{"x": item['week'], "y": item['total_sew'] or 0} for item in aggregated]
        fabric_data = [{"x": item['week'], "y": item['total_fab'] or 0} for item in aggregated]

        result = [
            {"name": "Sewing", "data": sewing_data},
            {"name": "Fabric", "data": fabric_data},
        ]

        return Response(result, status=http_status.HTTP_200_OK)

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
            .values(customer=F('customer'))
            .annotate(
                total_accepted=Sum('accepted'),
                total_sample=Sum('sample'),
            )
            .order_by('customer')
        )

        result = [
            {
                "label": item['customer'],
                "value": round((item['total_accepted'] / item['total_sample']) * 100, 2)
                if item['total_sample'] > 0 else 0,
            }
            for item in aggregated
        ]

        return Response(result, status=http_status.HTTP_200_OK)

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
            .values(team=F('team'))
            .annotate(
                total_accepted=Sum('accepted'),
                total_sample=Sum('sample'),
            )
            .order_by('team')
        )

        result = [
            {
                "label": f"{item['team']}",
                "value": round((item['total_accepted'] / item['total_sample']) * 100, 2)
                if item['total_sample'] > 0 else 0,
            }
            for item in aggregated
        ]

        return Response(result, status=http_status.HTTP_200_OK)


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
            return Response({"data": []})

        # GROUP BY style: SUM(defects_total) / SUM(sample) * 100
        annotated = queryset.annotate(
            total_defects=Sum('defects_total'),
            total_sample=Sum('sample'),
        ).values('style', 'total_defects', 'total_sample')

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

        return Response({"data": result})

    @action(detail=False, methods=['get'], url_path='aql-weekly')
    def aql_weekly(self, request):
        """
        GET /api/kpis/aql-weekly/

        Returns weekly AQL trend with trend line.
        Formula: AVG(defects_total / sample) * 100
        """
        queryset = self.get_filtered_queryset(self.get_queryset())

        if not queryset.exists():
            return Response({"data": []})

        # GROUP BY week: AVG(defects_total / sample) * 100
        annotated = queryset.annotate(
            week_avg=ExpressionWrapper(
                Avg(F('defects_total') * 1.0 / Case(
                    When(sample=0, then=1),
                    default=F('sample')
                )),
                output_field=FloatField()
            )
        ).values('week').order_by('week')

        # Build series data
        aql_data = []
        for row in annotated:
            week = row['week']
            aql = (row['week_avg'] or 0) * 100
            aql_data.append({"x": week, "y": round(aql, 2)})

        if not aql_data:
            return Response({"data": []})

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

        return Response({
            "data": [
                {"name": "AQL", "data": aql_data},
                {"name": "Trend", "data": trend_data},
            ]
        })

    @action(detail=False, methods=['get'], url_path='audited-pieces')
    def audited_pieces(self, request):
        """
        GET /api/kpis/audited-pieces/

        Returns weekly total of audited pieces (SUM of sample).
        """
        queryset = self.get_filtered_queryset(self.get_queryset())

        if not queryset.exists():
            return Response({"data": []})

        # GROUP BY week: SUM(sample)
        annotated = queryset.annotate(
            total_sample=Sum('sample')
        ).values('week', 'total_sample').order_by('week')

        pieces_data = []
        for row in annotated:
            pieces_data.append({
                "x": row['week'],
                "y": row['total_sample'] or 0
            })

        return Response({
            "data": [
                {"name": "Pieces", "data": pieces_data},
            ]
        })
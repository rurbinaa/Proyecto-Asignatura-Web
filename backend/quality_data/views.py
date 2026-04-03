from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from rest_framework import status as http_status
from django.shortcuts import get_object_or_404
import pandas as pd
import numpy as np
import datetime
from quality_data.models import QualityQcFa, SecondsA4, SecondsGeneral, Container, ExcelSyncSession
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
    parser_classes = [FileUploadParser]

    def post (self, request, filename, format = None):
        file_obj = request.data['file']

        # print_headers(file_obj, *SHEET_NAMES[0])
        # print_headers(file_obj, *SHEET_NAMES[1])
        # print_headers(file_obj, *SHEET_NAMES[2])
        # print_headers(file_obj, *SHEET_NAMES[3])
        # print_headers(file_obj, *SHEET_NAMES[4])


        qc_fa_plant_df = load_and_clean(
            file_obj,
            QC_FA_PLANT_REMAP,
            QC_FA_PLANT_NUMERIC_COLUMNS,
            QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
            *SHEET_NAMES[0],
        )

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
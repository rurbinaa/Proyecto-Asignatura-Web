from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from excel_importer.handler_service import load_and_clean, bulk_insert
from quality_data.models import QualityQcFa
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
)


def _get_incremental_rows(df, table_type):
    db_rows = QualityQcFa.objects.filter(defeacts__table_type=table_type).count()
    df_rows = len(df)
    rows_to_insert = max(df_rows - db_rows, 0)

    if rows_to_insert == 0:
        return df.iloc[0:0]

    return df.tail(rows_to_insert).copy()

class Process(APIView):
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

        load_and_clean(
            file_obj,
            QC_FA_CUSTOMER_REMAP,
            QC_FA_CUSTOMER_NUMERIC_COLUMNS,
            QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
            *SHEET_NAMES[1],
        )

        return Response(status = 204)
    

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

        qc_fa_plant_new_rows = _get_incremental_rows(qc_fa_plant_df, "QFA")
        bulk_insert(
            qc_fa_plant_new_rows,
            QC_FA_PLANT_NUMERIC_COLUMNS,
            QC_FA_PLANT_NOT_NUMERIC_COLUMNS,
            QC_FA_PLANT_AMOUNT_DEFEACTS_FIELDS,
            table_type="QFA",
        )

        qc_fa_customer_new_rows = _get_incremental_rows(qc_fa_customer_df, "QFC")
        bulk_insert(
            qc_fa_customer_new_rows,
            QC_FA_CUSTOMER_NUMERIC_COLUMNS,
            QC_FA_CUSTOMER_NOT_NUMERIC_COLUMNS,
            QC_FA_CUSTOMER_AMOUNT_DEFEACTS_FIELDS,
            table_type="QFC",
        )

        print(f"qc_fa_plant: {len(qc_fa_plant_new_rows)}")
        print(f"qc_fa_customer: {len(qc_fa_customer_new_rows)}")

        return Response(status = 204)
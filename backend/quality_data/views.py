from rest_framework.views import APIView
from rest_framework.parsers import FileUploadParser
from rest_framework.response import Response
from excel_importer.handler_service import (
    load_and_clean,
    bulk_insert,
    bulk_insert_seconds_a4,
    bulk_insert_seconds_general,
    bulk_insert_container,
    print_headers,
)
from quality_data.models import QualityQcFa, SecondsA4, SecondsGeneral, Container
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

def _get_incremental_rows(df, model_class, **filters):
    db_rows = model_class.objects.filter(**filters).count()
    df_rows = len(df)
    rows_to_insert = max(df_rows - db_rows, 0)

    if rows_to_insert == 0:
        return df.iloc[0:0]

    return df.tail(rows_to_insert).copy()

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


        print(f"qc_fa_plant: {len(qc_fa_plant_new_rows)}")
        print(f"qc_fa_customer: {len(qc_fa_customer_new_rows)}")
        print(f"seconds_a4: {len(seconds_a4_new_rows)}")
        print(f"seconds_general: {len(seconds_general_new_rows)}")
        print(f"container: {len(container_new_rows)}")

        return Response(status = 204)
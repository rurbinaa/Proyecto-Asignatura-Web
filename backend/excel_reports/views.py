from django.http import HttpResponse
from .services import ExcelService
import io
from media_data.models import RevisionDefect
from datetime import datetime

def prueba_carga(request):
    service = ExcelService('plantilla_corporativa.xlsx')
    wb = service.load_workbook()
    return HttpResponse("Template loaded successfully")

def generar_reporte(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if not start_date_str or not end_date_str:
        return HttpResponse("Missing start_date and end_date parameters (format YYYY-MM-DD)", status=400)
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return HttpResponse("Invalid date format. Use YYYY-MM-DD", status=400)
    
    # Validación de existencia de datos
    if not RevisionDefect.objects.filter(inspection__date__range=[start_date, end_date]).exists():
        return HttpResponse("No data in the selected date range", status=404)

    defects = RevisionDefect.objects.filter(
        inspection__date__range=[start_date, end_date]
    ).select_related('inspection', 'defect_type', 'inspection__color')
    
    service = ExcelService('plantilla_corporativa.xlsx')
    wb = service.load_workbook()
    sheet_name = wb.sheetnames[0]
    
    # Mapeo celular
    service.write_cell(sheet_name, 'A1', 'Date')
    service.write_cell(sheet_name, 'B1', 'Lot')
    service.write_cell(sheet_name, 'C1', 'Color')
    service.write_cell(sheet_name, 'D1', 'Defect Type')
    service.write_cell(sheet_name, 'E1', 'Size')
    service.write_cell(sheet_name, 'F1', 'Count')
    
    # Mapeo de registros a celdas
    for i, defect in enumerate(defects, start=2):
        service.write_cell(sheet_name, f'A{i}', str(defect.inspection.date))
        service.write_cell(sheet_name, f'B{i}', defect.inspection.lot or 'N/A')
        service.write_cell(sheet_name, f'C{i}', defect.inspection.color.name)
        service.write_cell(sheet_name, f'D{i}', defect.defect_type.name if defect.defect_type else 'N/A')
        service.write_cell(sheet_name, f'E{i}', defect.defect_size)
        service.write_cell(sheet_name, f'F{i}', defect.defect_count)
    
    # Guardado y respuesta HTTP
    output = io.BytesIO()
    service.save_workbook(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="report_{start_date}_{end_date}.xlsx"'
    return response
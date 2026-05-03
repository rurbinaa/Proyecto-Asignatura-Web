from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    Process, ExcelPreviewView, ExcelConfirmView, ExcelRejectView,
    TopDefectsView, FabricDefectsView, DefectsByStyleTypeView,
    KpiViewSet, AqlKpiViewSet,
    PassRejectDistributionView, RejectedEvolutionView,
    ContainersByStateView, DefectRateView,
    VolatileKpiView, FilterOptionsView, CorporateXlsxReportView,
)
from .views.seconds_gen_views import SecondsGeneralAnalyticsViewSet

app_name = 'quality_data'

# Router for ViewSet-based KPI endpoints
# Use distinct prefixes for each ViewSet to avoid duplicate /kpis/ routes.
router = DefaultRouter()
router.register(r'kpis/aql', AqlKpiViewSet, basename='kpi-aql')
router.register(r'kpis/rendimiento', KpiViewSet, basename='kpi-rendimiento')
router.register(r'kpis/seconds-general', SecondsGeneralAnalyticsViewSet, basename='seconds-general-analytics')

urlpatterns = [
    # Legacy endpoints (kept for backward compatibility)
    path(r'process/<str:filename>/', Process.as_view(), name='process'),

    # V2 endpoints — Preview → Confirm → Apply workflow
    path(r'excel/preview/<str:filename>/', ExcelPreviewView.as_view(), name='excel-preview'),
    path(r'excel/confirm/<int:session_id>/', ExcelConfirmView.as_view(), name='excel-confirm'),
    path(r'excel/reject/<int:session_id>/', ExcelRejectView.as_view(), name='excel-reject'),

    # Grupo 2 - KPIs Rendimiento (ViewSet with @action)
    path(r'', include(router.urls)),

    # Grupo 3 - KPIs Defectos
    path(r'kpis/top-defects/', TopDefectsView.as_view(), name='kpi-top-defects'),
    path(r'kpis/fabric-defects/', FabricDefectsView.as_view(), name='kpi-fabric-defects'),
    path(r'kpis/defects-by-style-type/', DefectsByStyleTypeView.as_view(), name='kpi-defects-by-style-type'),

    # Grupo 4 - KPIs Operativos
    path(r'kpis/pass-reject-distribution/', PassRejectDistributionView.as_view(), name='kpi-pass-reject-distribution'),
    path(r'kpis/rejected-evolution/', RejectedEvolutionView.as_view(), name='kpi-rejected-evolution'),
    path(r'kpis/containers-by-state/', ContainersByStateView.as_view(), name='kpi-containers-by-state'),
    path(r'kpis/defect-rate/', DefectRateView.as_view(), name='kpi-defect-rate'),

    # Volatile KPIs — Excel en memoria (sin DB)
    path(r'kpis/volatile/', VolatileKpiView.as_view(), name='kpi-volatile'),

    # Filter options — dynamic choices for filter selects/datalists
    path(r'kpis/filter-options/', FilterOptionsView.as_view(), name='kpi-filter-options'),

    # Corporate QA XLSX reports
    path(r'reports/corporate-xlsx/', CorporateXlsxReportView.as_view(), name='corporate-xlsx-report'),
]

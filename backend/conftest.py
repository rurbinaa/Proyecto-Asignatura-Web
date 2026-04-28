"""
Pytest configuration and shared fixtures for backend tests.
"""
import io
import pytest
import pandas as pd


@pytest.fixture
def seed_colors():
    """Create all COMPANY_COLORS entries idempotently via get_or_create."""
    from quality_data.models import Color
    from quality_data.init_data_models import COMPANY_COLORS
    for color_name in COMPANY_COLORS:
        Color.objects.get_or_create(name=color_name, defaults={"is_active": True})


@pytest.fixture
def seed_defect_types():
    """Create all GARMENT_DEFECT_TYPES entries idempotently via get_or_create."""
    from quality_data.models import DefectType
    from quality_data.init_data_models import GARMENT_DEFECT_TYPES
    for defect_name in GARMENT_DEFECT_TYPES:
        DefectType.objects.get_or_create(name=defect_name, defaults={"is_active": True})


@pytest.fixture
def seed_container_defect_types():
    """Create all CONTAINER_DEFECT_TYPES entries idempotently via get_or_create."""
    from quality_data.models import ContainerDefectType
    from quality_data.init_data_models import CONTAINER_DEFECT_TYPES
    for defect_name in CONTAINER_DEFECT_TYPES:
        ContainerDefectType.objects.get_or_create(name=defect_name, defaults={"is_active": True})


@pytest.fixture
def excel_file_factory():
    """
    Factory fixture that creates in-memory Excel files for testing.
    Returns a function that accepts df (DataFrame) and returns BytesIO.
    Does NOT persist any data to the database.
    """
    def _make_excel_file(df: pd.DataFrame, sheet_name: str = "Sheet1") -> io.BytesIO:
        """
        Create an in-memory Excel file from a DataFrame.

        Args:
            df: pandas DataFrame with the data
            sheet_name: name of the sheet (default "Sheet1")

        Returns:
            io.BytesIO object positioned at start, suitable for file upload simulation
        """
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        buffer.seek(0)
        return buffer

    return _make_excel_file


@pytest.fixture
def empty_excel_file(excel_file_factory):
    """Return an in-memory Excel file with no data (empty sheet)."""
    df = pd.DataFrame()
    return excel_file_factory(df)


@pytest.fixture
def qc_fa_plant_sample_data():
    """
    Return a sample DataFrame matching QC FA Plant structure
    with required columns for VolatileKpiView testing.
    """
    return pd.DataFrame({
        'date_1': ['2025-01-10', '2025-01-11', '2025-01-12'],
        'week': [1, 1, 2],
        'customer': ['CUST_A', 'CUST_A', 'CUST_B'],
        'team': [1, 2, 1],
        'coord': ['JAVIER', 'PEDRO', 'JAVIER'],
        'po': [100, 101, 102],
        'style': ['N3165', 'N3165', 'N4165'],
        'batch': [1, 1, 2],
        'color': ['red', 'blue', 'red'],
        'qty': [100, 100, 100],
        'seconds': [50, 50, 50],
        'accepted': [95, 90, 85],
        'rejected': [5, 10, 15],
        'sample': [100, 100, 100],
        'defects_total': [3, 5, 8],
        'aql': [2.5, 2.5, 2.5],
        'pass_or_fail': ['PASS', 'PASS', 'REJECT'],
        'sew_def': [2, 3, 5],
        'fab_def': [1, 2, 3],
    })


@pytest.fixture
def qc_fa_plant_single_row():
    """Return a DataFrame with a single row for trend calculation testing."""
    return pd.DataFrame({
        'date_1': ['2025-01-10'],
        'week': [1],
        'customer': ['CUST_A'],
        'team': [1],
        'coord': ['JAVIER'],
        'po': [100],
        'style': ['N3165'],
        'batch': [1],
        'color': ['red'],
        'qty': [100],
        'seconds': [50],
        'accepted': [95],
        'rejected': [5],
        'sample': [100],
        'defects_total': [3],
        'aql': [2.5],
        'pass_or_fail': ['PASS'],
        'sew_def': [2],
        'fab_def': [1],
    })


@pytest.fixture
def qc_fa_plant_zero_sample():
    """Return a DataFrame where sample=0 to test division by zero safety."""
    return pd.DataFrame({
        'date_1': ['2025-01-10', '2025-01-11'],
        'week': [1, 1],
        'customer': ['CUST_A', 'CUST_B'],
        'team': [1, 2],
        'coord': ['JAVIER', 'PEDRO'],
        'po': [100, 101],
        'style': ['N3165', 'N4165'],
        'batch': [1, 2],
        'color': ['red', 'blue'],
        'qty': [100, 100],
        'seconds': [50, 50],
        'accepted': [0, 0],
        'rejected': [0, 0],
        'sample': [0, 0],  # Zero sample!
        'defects_total': [0, 0],
        'aql': [2.5, 2.5],
        'pass_or_fail': ['PASS', 'PASS'],
        'sew_def': [0, 0],
        'fab_def': [0, 0],
    })


@pytest.fixture
def qc_fa_plant_missing_columns():
    """Return a DataFrame with missing columns to test _compute_filter_options."""
    return pd.DataFrame({
        'date_1': ['2025-01-10'],
        # Missing: week, customer, team, style, color, batch
        'po': [100],
        'accepted': [95],
        'rejected': [5],
        'sample': [100],
        'defects_total': [3],
    })

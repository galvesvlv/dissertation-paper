from pathlib import Path

from src.paths import (
    CAPITALS,
    ERA5_CAPITALS_DIR,
    ERA5_DAILY_DIR,
    ERA5_HOURLY_DIR,
    ERA5_MONTHLY_DIR,
    HEALTH_DEATHS_FILE,
    HEALTH_HOSPITALIZATIONS_FILE,
    XHWI_NETCDF,
    capital_monthly_files,
)


def test_all_capitals_have_twelve_monthly_files():
    assert len(CAPITALS) == 27
    for capital in CAPITALS:
        assert len(capital_monthly_files(capital)) == 12, capital


def test_required_raw_files_exist():
    assert XHWI_NETCDF.is_file()
    assert HEALTH_DEATHS_FILE.is_file()
    assert HEALTH_HOSPITALIZATIONS_FILE.is_file()


def test_intermediate_capital_products_are_in_expected_layers():
    for capital in CAPITALS:
        assert (ERA5_HOURLY_DIR / capital).is_dir()
        assert (ERA5_DAILY_DIR / capital).is_dir()
        assert (ERA5_MONTHLY_DIR / capital).is_dir()
        assert next((ERA5_HOURLY_DIR / capital).glob("*.parquet"), None)
        assert next((ERA5_DAILY_DIR / capital).glob("*.parquet"), None)
        assert next((ERA5_MONTHLY_DIR / capital).glob("*.parquet"), None)


def test_paths_are_project_relative():
    project_root = Path(__file__).resolve().parents[1]
    assert str(project_root) in str(ERA5_CAPITALS_DIR)
    assert "/content/drive" not in str(ERA5_CAPITALS_DIR)

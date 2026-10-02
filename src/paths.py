"""Centralized project paths and study metadata.

All paths are derived from this file location, so notebooks do not depend on
Google Drive, a user's home directory, or the current working directory.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERMEDIATE_DATA_DIR = DATA_DIR / "intermediate"
RESULTS_DIR = PROJECT_ROOT / "results"

ERA5_CAPITALS_DIR = RAW_DATA_DIR / "era5" / "capitals"
XHWI_NETCDF = RAW_DATA_DIR / "era5" / "brazil_xhwi_monthly.nc"
HEALTH_CAPITALS_DIR = RAW_DATA_DIR / "health" / "capitals"
HEALTH_DEATHS_FILE = HEALTH_CAPITALS_DIR / "capitals_deaths_1996-2023.csv"
HEALTH_HOSPITALIZATIONS_FILE = HEALTH_CAPITALS_DIR / "capitals_hospitalizations_1996-2023.csv"
GEO_DIR = RAW_DATA_DIR / "geospatial"
ADMINISTRATIVE_DIR = GEO_DIR / "administrative"
LEGAL_AMAZON_DIR = GEO_DIR / "legal_amazon"
ELDERLY_DIR = GEO_DIR / "elderly_population"
TRADITIONAL_COMMUNITIES_DIR = GEO_DIR / "traditional_communities"

ERA5_HOURLY_DIR = INTERMEDIATE_DATA_DIR / "era5" / "capitals" / "hourly"
ERA5_DAILY_DIR = INTERMEDIATE_DATA_DIR / "era5" / "capitals" / "daily"
ERA5_MONTHLY_DIR = INTERMEDIATE_DATA_DIR / "era5" / "capitals" / "monthly"
CAPITAL_AGGREGATES_DIR = INTERMEDIATE_DATA_DIR / "era5" / "capital_aggregates"
CLUSTERING_METRICS_FILE = INTERMEDIATE_DATA_DIR / "clustering_monthly_metrics.parquet"

START_DATE = "1950-01-01"
END_DATE = "2023-12-31"
REFERENCE_START_YEAR = 1961
REFERENCE_END_YEAR = 1990
PERIODS = {
    "P1": (1950, 1974),
    "P2": (1975, 1998),
    "P3": (1999, 2023),
}

CAPITALS = {
    "Porto Velho": "RO", "Rio Branco": "AC", "Manaus": "AM",
    "Boa Vista": "RR", "Belém": "PA", "Macapá": "AP", "Palmas": "TO",
    "São Luís": "MA", "Teresina": "PI", "Fortaleza": "CE", "Natal": "RN",
    "João Pessoa": "PB", "Recife": "PE", "Maceió": "AL", "Aracaju": "SE",
    "Salvador": "BA", "Belo Horizonte": "MG", "Vitória": "ES",
    "Rio de Janeiro": "RJ", "São Paulo": "SP", "Curitiba": "PR",
    "Florianópolis": "SC", "Porto Alegre": "RS", "Campo Grande": "MS",
    "Cuiabá": "MT", "Goiânia": "GO", "Brasília": "DF",
}
UF_TO_CAPITAL = {uf: capital for capital, uf in CAPITALS.items()}

HEATWAVE_METRICS = [
    "Ind_Prod_Monthly", "ind_prod_monthly_qtd", "ind_prod_3episodes",
    "ind_prod_5episodes", "noaa_qtd_monthly", "noaa_3episodes",
    "noaa_5episodes", "omm_qtd_monthly", "omm_3episodes", "omm_5episodes",
    "NOAA_HWI_mean", "NOAA_HWI_max", "NOAA_HWI_min",
    "caution_qtd_hr_month", "extreme_caution_qtd_hr_month",
    "danger_qtd_hr_month", "extreme_danger_qtd_hr_month",
]

SEASONS = {
    "DJF": [12, 1, 2],
    "MAM": [3, 4, 5],
    "JJA": [6, 7, 8],
    "SON": [9, 10, 11],
}

REGIONS = {
    "N": ["RO", "AC", "AM", "RR", "PA", "AP", "TO"],
    "NE": ["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"],
    "SE": ["MG", "ES", "RJ", "SP"],
    "S": ["PR", "SC", "RS"],
    "CW": ["MS", "MT", "GO", "DF"],
}


def capital_monthly_files(capital: str) -> list[Path]:
    """Return the twelve raw monthly files for one capital."""
    directory = ERA5_CAPITALS_DIR / capital
    return sorted(directory.glob(f"{capital}_heatwave_ERA5_month_*.csv"))


def ensure_result_directories() -> None:
    """Create documented result directories when a pipeline is executed."""
    for name in (
        "trend_analysis", "clustering", "period_comparison",
        "health_correlations", "hazard_maps", "vulnerability_maps", "risk_maps",
    ):
        (RESULTS_DIR / name).mkdir(parents=True, exist_ok=True)

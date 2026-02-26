"""
Eurostat GDP data provider for NUTS 3 regions.

This module retrieves Gross Domestic Product (GDP) statistics from the Eurostat API
for EU NUTS 3 regions. Data includes total GDP (in millions PPS) and per-capita GDP
(in PPS per inhabitant) for the year 2024.

Reference:
    Eurostat SDMX-ML API: https://ec.europa.eu/eurostat/web/json-and-unicode-web-services
    GDP dataset: nama_10r_3gdp (GDP at current market prices by NUTS 3 region)
"""

import logging
from typing import Dict, List

import pandas as pd
import requests

logger = logging.getLogger(__name__)

# Eurostat API configuration
EUROSTAT_API_URL = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_3gdp"
)
EUROSTAT_API_TIMEOUT = 30  # seconds
EUROSTAT_API_YEAR = "2024"


def _parse_sdmx_values(data: Dict) -> pd.DataFrame:
    """Parse SDMX-ML JSON response into a long-form DataFrame.

    The Eurostat API returns values indexed as either colon-separated indices
    (e.g., "0:1:0") or flat indices depending on the dataset structure.
    This function converts both formats to a long-form table with one row per
    dimension combination.

    Args:
        data: Raw SDMX-ML JSON response from Eurostat API.

    Returns:
        DataFrame with columns for each dimension (geo, unit, time) and a 'value' column.

    Raises:
        KeyError: If expected keys are missing in the response.
    """
    dims = data["dimension"]
    dim_names = list(dims.keys())

    # Build index mappings for each dimension
    codes_lists = [list(dims[d]["category"]["index"].keys()) for d in dim_names]
    sizes = [len(lst) for lst in codes_lists]

    rows: List[Dict] = []
    for key, value in data.get("value", {}).items():
        # Parse the key (either colon-separated or flat integer)
        parts = key.split(":")
        if len(parts) == len(dim_names):
            idxs = list(map(int, parts))
        else:
            # Flat index: convert to multi-dimensional indices
            flat = int(parts[0])
            idxs = []
            for size in reversed(sizes):
                idxs.append(flat % size)
                flat //= size
            idxs = list(reversed(idxs))

        # Build row with dimension codes and value
        row = {dim_names[i]: codes_lists[i][idxs[i]] for i in range(len(dim_names))}
        row["value"] = value
        rows.append(row)

    return pd.DataFrame(rows)


def _fetch_gdp_data(year: str = EUROSTAT_API_YEAR) -> pd.DataFrame:
    """Fetch GDP data from Eurostat API for a given year.

    Args:
        year: Year for which to retrieve data (default: 2024).

    Returns:
        DataFrame with three columns: nut3_code, gdp_total (millions PPS),
        and gdp_per_capita (PPS per inhabitant).

    Raises:
        requests.exceptions.RequestException: If API request fails.
    """
    logger.info(f"Fetching GDP data from Eurostat for year {year}")

    params = {"time": year}
    response = requests.get(
        EUROSTAT_API_URL,
        params=params,
        timeout=EUROSTAT_API_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()

    logger.debug(f"Received {len(data.get('value', {}))} value records from API")

    # Parse SDMX JSON to long format
    df_long = _parse_sdmx_values(data)

    # Pivot to wide format with geo as index and unit as columns
    df_wide = (
        df_long.pivot(index="geo", columns="unit", values="value")
        .reset_index()
    )

    columns_renaming = {
        "geo": "nut3_code", "MIO_PPS_EU27_2020": "pps", "PPS_EU27_2020_HAB": "pps_per_inhabitant"
    }

    df_result = df_wide.rename(columns=columns_renaming)
    df_result = df_result[list(columns_renaming.values())]

    logger.info(f"Successfully retrieved GDP data for {len(df_result)} NUTS 3 regions")

    return df_result


def load_nuts3_gdp(year: str = EUROSTAT_API_YEAR) -> pd.DataFrame:
    """Load GDP statistics for EU NUTS 3 regions.

    Retrieves and aggregates Gross Domestic Product (GDP) data from the Eurostat
    API for the specified year. Returns a clean DataFrame with regional GDP metrics
    suitable for analysis and integration with other geographic datasets.

    Args:
        year: Year for which to retrieve data. Defaults to 2024.
             Eurostat typically provides data with a 1-2 year lag.

    Returns:
        DataFrame with columns:
            - nut3_code (str): NUTS 3 region code (e.g., 'DE001')
            - gdp_total (float): Gross Domestic Product in millions of PPS
            - gdp_per_capita (float): GDP per capita in PPS per inhabitant

    Examples:
        >>> gdp_df = load_nuts3_gdp()
        >>> gdp_df.head()
           nut3_code  gdp_total  gdp_per_capita
        0      FR101   123456.5          45678.9
        1      DE101   234567.2          56789.1

    Raises:
        requests.exceptions.RequestException: If the API request fails.
        KeyError: If the response format is unexpected.
    """
    return _fetch_gdp_data(year)
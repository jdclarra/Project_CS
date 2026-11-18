"""
external_data.py - Exchange Cost Planner

Data that we load live from two free online APIs (no API key needed):

1. Open-Meteo archive API   -> climate during the exchange semester
2. IMF DataMapper API       -> inflation since 2022, to update the Kaggle prices

Both functions return None if the request fails (no internet, server
down, timeout). The app then shows a warning instead of crashing.
"""

from datetime import date

import pandas as pd
import requests

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

NUMBER_OF_CLIMATE_YEARS = 3   # we average the weather of the last 3 complete years

# 1. Climate (Open-Meteo)

def get_monthly_climate(latitude, longitude):
    """Average temperature and rain per month for a place.

    A real weather forecast for a semester that starts in several months
    does not exist. Instead we look at what the weather was like in the
    last 3 complete years and average it per month ("climate").

    How it works:
    1. Our app sends an HTTP GET request with the coordinates and dates.
    2. The Open-Meteo server answers with JSON: one value per day.
    3. response.json() turns the JSON text into a Python dictionary,
       which we put into a pandas DataFrame and summarise per month.

    Returns a DataFrame with 12 rows (month, month_name, temperature_c,
    rain_mm) or None if the request fails.
    """
    last_complete_year = date.today().year - 1
    first_year = last_complete_year - NUMBER_OF_CLIMATE_YEARS + 1

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": f"{first_year}-01-01",
        "end_date": f"{last_complete_year}-12-31",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()  # error if the status code is 4xx or 5xx
        data = response.json()
        daily = pd.DataFrame({
            "date": pd.to_datetime(data["daily"]["time"]),
            "temp_max": data["daily"]["temperature_2m_max"],
            "temp_min": data["daily"]["temperature_2m_min"],
            "rain_mm": data["daily"]["precipitation_sum"],
        })
    except Exception:
        return None

    # Daily mean temperature = average of the daily maximum and minimum
    daily["temperature_c"] = (daily["temp_max"] + daily["temp_min"]) / 2
    daily["month"] = daily["date"].dt.month

    # Data wrangling: about 1,100 daily rows -> 12 monthly rows
    temperature_per_month = daily.groupby("month")["temperature_c"].mean()
    # Rain: total of all days of that month over 3 years, divided by 3 = rain in an average month
    rain_per_month = daily.groupby("month")["rain_mm"].sum() / NUMBER_OF_CLIMATE_YEARS

    climate = pd.DataFrame({
        "month": temperature_per_month.index,
        "temperature_c": temperature_per_month.values.round(1),
        "rain_mm": rain_per_month.values.round(0),
    })
    climate["month_name"] = [MONTH_NAMES[number - 1] for number in climate["month"]]
    return climate

# 2. Inflation (IMF DataMapper) 
def get_inflation_factor(iso3):
    """How much consumer prices rose from Dec 2022 to 2026 (IMF DataMapper API, no key).
    Returns e.g. 1.12 for +12 %, or None if the API cannot be reached."""
    try:
        url = f"https://www.imf.org/external/datamapper/api/v1/PCPIPCH/{iso3}"
        rates = requests.get(url, timeout=5).json()["values"]["PCPIPCH"][iso3]
        factor = 1.0
        for year in ["2023", "2024", "2025", "2026"]:
            factor = factor * (1 + rates.get(year, 0) / 100)
        return factor
    except Exception:
        return None


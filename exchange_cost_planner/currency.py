"""

Gets current exchange rates from the free Frankfurter API
(https://frankfurter.dev, rates of the European Central Bank, no API key)
and converts CHF amounts into the local currency of the exchange city.

If the API cannot be reached, we use the last rates that were saved in
data/last_rates.json, so the app keeps working (with a note that the
rates are not live).

"""


# Declaration of AI Assistance: reading and writing a JSON file (json, os, "with open(...)") is not
# part of our course. The file handling in save_rates and load_saved_rates was written with Claude.
import json
import os

import requests

API_URL = "https://api.frankfurter.dev/v1/latest"

PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
SAVED_RATES_PATH = os.path.join(PROJECT_FOLDER, "data", "last_rates.json")


# Saving and loading rates (file handling)
def save_rates(rates, rates_date):
    """Write the rates into a JSON file, so we can use them if the API is down."""
    os.makedirs(os.path.dirname(SAVED_RATES_PATH), exist_ok=True)
    with open(SAVED_RATES_PATH, "w") as file:
        json.dump({"date": rates_date, "rates": rates}, file, indent=2)


def load_saved_rates():
    """Read the saved rates. Returns (rates, date) or (None, None) if there is no file."""
    if not os.path.exists(SAVED_RATES_PATH):
        return None, None
    try:
        with open(SAVED_RATES_PATH) as file:
            saved = json.load(file)
        return saved["rates"], saved["date"]
    except Exception:
        # File is damaged or has the wrong format
        return None, None


# API requests
# Declaration of AI Assistance: requests.get with params and .json() is part of our course.
# The timeout, raise_for_status and the error handling with try / except were written with Claude.
def get_exchange_rates(currencies):
    """Get today's value of 1 CHF in each of the given currencies.

    currencies: list of currency codes, e.g. ["EUR", "USD", "SGD"]

    How it works:
    1. Our app sends an HTTP GET request to the Frankfurter server.
    2. The server answers with JSON, e.g.
       {"amount": 1.0, "base": "CHF", "date": "2026-10-30", "rates": {"EUR": 1.07, "USD": 1.25}}
    3. response.json() turns this text into a Python dictionary.

    Returns two values: (rates, source)
      rates  - dictionary like {"CHF": 1.0, "EUR": 1.07, ...} or None if no rates are available
      source - text for the app, e.g. "live (ECB, 2026-10-30)" or "saved rates from 2026-10-28"
    """
    # We only need to ask for currencies other than CHF
    other_currencies = []
    for currency in currencies:
        if currency != "CHF" and currency not in other_currencies:
            other_currencies.append(currency)

    if len(other_currencies) == 0:
        return {"CHF": 1.0}, "no conversion needed"

    try:
        response = requests.get(
            API_URL,
            params={"base": "CHF", "symbols": ",".join(other_currencies)},
            timeout=5,
        )
        response.raise_for_status()  # error if the status code is 4xx or 5xx
        data = response.json()

        rates = data["rates"]
        rates["CHF"] = 1.0
        save_rates(rates, data["date"])
        return rates, f"live (ECB, {data['date']})"

    except Exception:
        # No internet, server down, or unknown currency -> try the saved rates
        saved_rates, saved_date = load_saved_rates()
        if saved_rates is None:
            return None, "not available"

        # Only use the saved rates if they contain all currencies we need
        for currency in other_currencies:
            if currency not in saved_rates:
                return None, "not available"
        return saved_rates, f"saved rates from {saved_date} (API not reachable)"


# Conversion
def convert_from_chf(amount_chf, rate):
    """Convert an amount from CHF into the local currency.

    rate = value of 1 CHF in the local currency (from get_exchange_rates)
    Example: convert_from_chf(1000, 1.07) -> 1070 (EUR)
    """
    return round(amount_chf * rate)

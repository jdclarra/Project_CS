"""
currency_converter – Feature for the Exchange Cost Planner

Shows the local currency of the chosen exchange city and its current exchange rate,
e.g. Madrid -> EUR -> "1 EUR = 0.93 CHF".

Data source: Frankfurter API (https://frankfurter.dev), free, no API key needed,
rates are updated once per working day.

Test this feature on its own:   streamlit run currency_converter.py
Use it in the main code:        from currency_converter import currency_converter
                                currency_converter(city)
"""

import requests                # for sending HTTP requests to the API
import json                    # only needed for printing the JSON response while testing
import streamlit as st


# Which currency is used in which exchange city.
# Built from our cities.csv (columns city + currency) - all 134 partner cities.
# The city names must be spelled exactly like in cities.csv.
CITY_CURRENCIES = {
    "Ahmedabad":                   "INR",   # India
    "Alajuela":                    "CRC",   # Costa Rica
    "Ann Arbor":                   "USD",   # USA
    "Atlanta":                     "USD",   # USA
    "Austin":                      "USD",   # USA
    "Bangalore":                   "INR",   # India
    "Bangkok":                     "THB",   # Thailand
    "Barcelona":                   "EUR",   # Spain
    "Basel":                       "CHF",   # Switzerland
    "Beijing":                     "CNY",   # China
    "Beirut":                      "LBP",   # Lebanon
    "Berekuso":                    "GHS",   # Ghana
    "Bergen":                      "NOK",   # Norway
    "Berlin":                      "EUR",   # Germany
    "Bern":                        "CHF",   # Switzerland
    "Bloomington (Indiana)":       "USD",   # USA
    "Bogotá":                      "COP",   # Colombia
    "Bologna":                     "EUR",   # Italy
    "Bordeaux":                    "EUR",   # France
    "Boston":                      "USD",   # USA
    "Brisbane":                    "AUD",   # Australia
    "Budapest":                    "HUF",   # Hungary
    "Buenos Aires":                "ARS",   # Argentina
    "Cairo":                       "EGP",   # Egypt
    "Cape Town":                   "ZAR",   # South Africa
    "Caracas":                     "VES",   # Venezuela
    "Chapel Hill":                 "USD",   # USA
    "Charlottesville":             "USD",   # USA
    "Chicago":                     "USD",   # USA
    "Claremont (California)":      "USD",   # USA
    "Cologne":                     "EUR",   # Germany
    "Columbia (South Carolina)":   "USD",   # USA
    "Copenhagen":                  "DKK",   # Denmark
    "Coventry":                    "GBP",   # United Kingdom
    "Dar es Salaam":               "TZS",   # Tanzania
    "Dubai":                       "AED",   # United Arab Emirates
    "Dublin":                      "EUR",   # Ireland
    "Dunedin":                     "NZD",   # New Zealand
    "Durham (North Carolina)":     "USD",   # USA
    "Edinburgh":                   "GBP",   # United Kingdom
    "Frankfurt am Main":           "EUR",   # Germany
    "Fribourg":                    "CHF",   # Switzerland
    "Geneva":                      "CHF",   # Switzerland
    "George Town (Penang)":        "MYR",   # Malaysia
    "Gothenburg":                  "SEK",   # Sweden
    "Haifa":                       "ILS",   # Israel
    "Hamburg":                     "EUR",   # Germany
    "Hanover (New Hampshire)":     "USD",   # USA
    "Helsinki":                    "EUR",   # Finland
    "Hong Kong":                   "HKD",   # China (Hong Kong SAR)
    "Hyderabad":                   "INR",   # India
    "Istanbul":                    "TRY",   # Turkey
    "Ithaca":                      "USD",   # USA
    "Johannesburg":                "ZAR",   # South Africa
    "Jönköping":                   "SEK",   # Sweden
    "Kingston (Ontario)":          "CAD",   # Canada
    "Kolkata":                     "INR",   # India
    "Kristiansand":                "NOK",   # Norway
    "Lancaster":                   "GBP",   # United Kingdom
    "Las Palmas de Gran Canaria":  "EUR",   # Spain
    "Lausanne":                    "CHF",   # Switzerland
    "Liberec":                     "CZK",   # Czech Republic
    "Lima":                        "PEN",   # Peru
    "Lisbon":                      "EUR",   # Portugal
    "London":                      "GBP",   # United Kingdom
    "London (Ontario)":            "CAD",   # Canada
    "Los Angeles":                 "USD",   # USA
    "Louvain-la-Neuve":            "EUR",   # Belgium
    "Lucerne":                     "CHF",   # Switzerland
    "Lugano":                      "CHF",   # Switzerland
    "Lund":                        "SEK",   # Sweden
    "Lyon":                        "EUR",   # France
    "Maastricht":                  "EUR",   # Netherlands
    "Madrid":                      "EUR",   # Spain
    "Manchester":                  "GBP",   # United Kingdom
    "Manila":                      "PHP",   # Philippines
    "Mannheim":                    "EUR",   # Germany
    "Medellín":                    "COP",   # Colombia
    "Medford":                     "USD",   # USA
    "Melbourne":                   "AUD",   # Australia
    "Mexico City":                 "MXN",   # Mexico
    "Mikkeli":                     "EUR",   # Finland
    "Milan":                       "EUR",   # Italy
    "Minamiuonuma":                "JPY",   # Japan
    "Minneapolis":                 "USD",   # USA
    "Monterrey":                   "MXN",   # Mexico
    "Montevideo":                  "UYU",   # Uruguay
    "Montreal":                    "CAD",   # Canada
    "Moscow":                      "RUB",   # Russia
    "Nagoya":                      "JPY",   # Japan
    "Neuchâtel":                   "CHF",   # Switzerland
    "New York":                    "USD",   # USA
    "Nice":                        "EUR",   # France
    "Oslo":                        "NOK",   # Norway
    "Oviedo":                      "EUR",   # Spain
    "Pamplona":                    "EUR",   # Spain
    "Paris":                       "EUR",   # France
    "Perth":                       "AUD",   # Australia
    "Prague":                      "CZK",   # Czech Republic
    "Pullman":                     "USD",   # USA
    "Quebec City":                 "CAD",   # Canada
    "Reims":                       "EUR",   # France
    "Rio de Janeiro":              "BRL",   # Brazil
    "Rome":                        "EUR",   # Italy
    "Rotterdam":                   "EUR",   # Netherlands
    "Safat":                       "KWD",   # Kuwait
    "Salzburg":                    "EUR",   # Austria
    "Santa Clara (California)":    "USD",   # USA
    "Santiago":                    "CLP",   # Chile
    "Seoul":                       "KRW",   # South Korea
    "Shanghai":                    "CNY",   # China
    "Shenzhen":                    "CNY",   # China
    "Singapore":                   "SGD",   # Singapore
    "St. Petersburg":              "RUB",   # Russia
    "Stellenbosch":                "ZAR",   # South Africa
    "Stockholm":                   "SEK",   # Sweden
    "Sydney":                      "AUD",   # Australia
    "São Paulo":                   "BRL",   # Brazil
    "Taipei":                      "TWD",   # Taiwan
    "Tel Aviv":                    "ILS",   # Israel
    "Tokyo":                       "JPY",   # Japan
    "Toronto":                     "CAD",   # Canada
    "Turin":                       "EUR",   # Italy
    "Vancouver":                   "CAD",   # Canada
    "Victoria (British Columbia)": "CAD",   # Canada
    "Vienna":                      "EUR",   # Austria
    "Viña del Mar":                "CLP",   # Chile
    "Warsaw":                      "PLN",   # Poland
    "Washington DC":               "USD",   # USA
    "Wellington":                  "NZD",   # New Zealand
    "Wollongong":                  "AUD",   # Australia
    "Yogyakarta":                  "IDR",   # Indonesia
    "Zagreb":                      "EUR",   # Croatia
    "Zurich":                      "CHF",   # Switzerland
}

# Currencies the user can compare the local currency with
TARGET_CURRENCIES = ["CHF", "EUR", "USD", "GBP"]


def get_city_currency(city):
    """Returns the currency of a city, e.g. 'Madrid' -> 'EUR'."""
    return CITY_CURRENCIES[city]


@st.cache_data(ttl=3600)   # Streamlit remembers the result for 1 hour, so we don't ask the API on every click
def get_exchange_rate(from_currency, to_currency):
    """
    Sends a request to the Frankfurter API and returns the current exchange rate
    and its date as a tuple, e.g. get_exchange_rate('EUR', 'CHF') -> (0.93, '2026-11-13')
    """
    url = 'https://api.frankfurter.dev/v2/rates'

    params = {}
    params['base'] = from_currency
    params['quotes'] = to_currency

    r = requests.get(url, params=params)
    # Uncomment the next line to see the JSON response of the API
    # print(json.dumps(r.json(), ensure_ascii=False, indent=4))

    # The response is a list with one entry per quote currency, e.g.
    # [{"date": "2026-11-13", "base": "EUR", "quote": "CHF", "rate": 0.93}]
    first_rate = r.json()[0]

    rate = first_rate['rate']
    date = first_rate['date']

    return (rate, date)


def find_unsupported_currencies():
    """Returns a list of the currencies in CITY_CURRENCIES that the Frankfurter API does not know."""
    url = 'https://api.frankfurter.dev/v2/currencies'

    r = requests.get(url)

    supported = []
    for c in r.json():
        supported.append(c['iso_code'])

    unsupported = []
    for currency in set(CITY_CURRENCIES.values()):
        if currency not in supported:
            unsupported.append(currency)
    return sorted(unsupported)


def currency_converter(city):
    """Shows a box with the local currency of the city and its current exchange rate."""
    local_currency = get_city_currency(city)

    with st.container(border=True):
        st.subheader("Exchange rate")
        st.write(f"Local currency in {city}: **{local_currency}**")

        # The user chooses which currency to compare with (without the local currency itself)
        options = []
        for c in TARGET_CURRENCIES:
            if c != local_currency:
                options.append(c)
        target_currency = st.selectbox("Compare with", options, key="currency_converter_target")

        # If the API is not reachable or does not know the currency, show a message instead of crashing
        try:
            rate, date = get_exchange_rate(local_currency, target_currency)
        except Exception:
            st.warning("The exchange rate is not available right now.")
            return

        st.metric(f"1 {local_currency} in {target_currency}", f"{rate:,.4f} {target_currency}")
        st.caption(f"1 {target_currency} = {1 / rate:,.4f} {local_currency} · rate from {date} · source: Frankfurter API")


# Only runs when this file is started directly (not when it is imported into the main code)
if __name__ == "__main__":
    st.title("Currency converter – test")
    city = st.selectbox("City", list(CITY_CURRENCIES))
    currency_converter(city)

    if st.button("Check: does the API support all our currencies?"):
        unsupported = find_unsupported_currencies()
        if unsupported:
            st.warning(f"Not supported by the API: {', '.join(unsupported)}")
        else:
            st.success("All our currencies are supported.")

# Exchange Cost Planner

A Streamlit web app to estimate the costs of an exchange.

## Data sources

### Data in the repository

- **Partner universities** (`data/universities.csv` → table `universities`)
  Source: HSG Mobility-Online portal and the HSG list of partner universities.

- **Cities and prices** (`data/cities.csv` → table `cities`)
  Source: Kaggle "Global Cost of Living" dataset (Numbeo, Dec 2022) and HSG experience reports.

- **Reported monthly costs** (`data/experiences.csv` → table `experiences`)
  Source: our survey and HSG experience reports.

### Live APIs

We use three free APIs. None of them needs an API key.

- **Frankfurter** (exchange rates CHF → local currency)
  Link: https://api.frankfurter.dev/v1/latest
  The rates are the reference rates of the European Central Bank. The last rates are saved in `data/last_rates.json` as a fallback if the API is not reachable.

- **Open-Meteo Archive** (daily temperature and precipitation of the last 3 complete years)
  Link: https://archive-api.open-meteo.com/v1/archive
  Free for non-commercial use. Attribution: Open-Meteo.com

- **IMF DataMapper** (yearly consumer price inflation per country, 2023 to 2026)
  Link: https://www.imf.org/external/datamapper/api/v1/PCPIPCH/<ISO3>
  `<ISO3>` is the three-letter country code (e.g. `CHE` for Switzerland). We use the inflation factor to bring the Kaggle prices from 2022 to today.


## Installation

Python 3.10 or newer.

```bash
cd exchange_cost_planner
pip install -r requirements.txt
```

On a Mac use `python3 -m pip install -r requirements.txt`.

## How to run

```bash
python create_database.py     # only needed after changing the CSV files
streamlit run app.py
```

On a Mac: `python3 create_database.py` and `python3 -m streamlit run app.py`.
The browser opens at <http://localhost:8501>. Stop the app with Ctrl + C.

Check the calculations: `python check_calculation.py` (must end with "All 26 checks passed.").

## Files

```
exchange_cost_planner/
├── app.py                 # App & Design: pages, inputs, results, charts, integration
├── database.py            # Daten & Datenbank: all SQL queries
├── create_database.py     # Daten & Datenbank: builds the SQLite database from the CSV files
├── calculation.py         # Berechnung & Wechselkurse: rule-based cost estimate
├── currency.py            # Berechnung & Wechselkurse: exchange rates (Frankfurter API)
├── check_calculation.py   # Berechnung & Wechselkurse: hand-calculated checks
├── ml_model.py            # Machine Learning: features, training, evaluation, prediction
├── external_data.py       # Externe Daten: climate (Open-Meteo) and inflation (IMF)
├── data/universities.csv  # 222 HSG partner universities, their city and study level
├── data/cities.csv        # 134 cities; prices in CHF for 117 of them
├── data/experiences.csv   # reported monthly costs
├── data/last_rates.json   # last exchange rates, used when the Frankfurter API cannot be reached
├── database/exchange_costs.db
├── requirements.txt
├── README.md             
└── CONTRIBUTIONS.md       # contribution matrix
 
```

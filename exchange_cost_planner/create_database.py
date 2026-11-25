"""

Run this script to build the SQLite database used by the app:

    python create_database.py

It reads three CSV files and stores them in database/exchange_costs.db:

1. data/cities.csv        -> table "cities"        (cost data per city, all amounts in CHF)
2. data/universities.csv  -> table "universities"  (HSG partner universities and their city)
3. data/experiences.csv   -> table "experiences"   (monthly costs of former exchange students,
                                                    the training data for our ML model)

The old database file is deleted first, so every run starts from scratch.

IMPORTANT: data honesty:
- Prices in data/cities.csv come from two sources (all amounts in CHF):
  * HSG experience reports 2023-2026 (price_base_year = 2026, median of all reports).
    Gaps in these cities were filled with Kaggle prices where possible.
  * The Kaggle "Global Cost of Living" dataset (Numbeo, Dec 2022, price_base_year = 2022),
    adjusted for inflation in the app (IMF API).
- Where neither source has a price, the field is empty ("NO DATA" in the column "source").
- If data/experiences.csv does not exist, this script creates a SIMULATED
  file, clearly labelled with source = "simulated". 
"""


import os
import sqlite3

import numpy as np
import pandas as pd

from calculation import HOUSING_COLUMNS, LIFESTYLES, PRICE_COLUMNS, calculate_monthly_costs

# Build paths relative to THIS file, so the script works from any folder
PROJECT_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(PROJECT_FOLDER, "database", "exchange_costs.db")
CITIES_CSV = os.path.join(PROJECT_FOLDER, "data", "cities.csv")
UNIVERSITIES_CSV = os.path.join(PROJECT_FOLDER, "data", "universities.csv")
EXPERIENCES_CSV = os.path.join(PROJECT_FOLDER, "data", "experiences.csv")

NUMBER_OF_SIMULATED_ROWS = 300

# All columns of the table "cities", in the same order as in CREATE TABLE below.
# If you add a column, add it here AND in CREATE TABLE.
# (cities.csv has a few more columns, e.g. leisure_month. The app does not use them,
# so they are not copied into the database.)
CITY_COLUMNS = [
    "city", "country", "iso3", "currency", "latitude", "longitude",
    "rent_shared_room", "rent_dorm", "rent_apartment",
    "groceries_month", "restaurant_meal", "evening_out", "transport_pass",
    "price_base_year", "source", "as_of_date",
]


# Simulated training data 
def simulate_experiences(cities):
    """Create fictional "experience reports" of former exchange students.

    For each fictional student we pick a random city, housing type, lifestyle
    and number of trips, calculate the monthly cost with our own cost
    calculator and add random noise, because real people never spend
    exactly what a formula says.
    """
    # Fixed seed -> every team member gets exactly the same simulated data
    rng = np.random.default_rng(seed=2026)

    # Only cities with a complete set of prices can be simulated
    cities = cities.dropna(subset=PRICE_COLUMNS).reset_index(drop=True)
    housing_types = list(HOUSING_COLUMNS.keys())
    lifestyles = list(LIFESTYLES.keys())

    rows = []
    for i in range(NUMBER_OF_SIMULATED_ROWS):
        city = cities.iloc[rng.integers(len(cities))]
        housing_type = housing_types[rng.integers(len(housing_types))]
        lifestyle = lifestyles[rng.integers(len(lifestyles))]
        trips_per_month = int(rng.integers(0, 5))

        monthly_costs = calculate_monthly_costs(city, housing_type, lifestyle, trips_per_month)
        expected_cost = sum(monthly_costs.values())

        # Real spending differs from the formula: on average +/- 12 %
        real_cost = expected_cost * rng.normal(1.0, 0.12)

        rows.append({
            "city": city["city"],
            "housing_type": housing_type,
            "lifestyle": lifestyle,
            "trips_per_month": trips_per_month,
            "monthly_cost_chf": int(round(real_cost, -1)),  # round to CHF 10
            "source": "simulated",
        })
    return pd.DataFrame(rows)


# Building the database
def create_tables(cursor):
    cursor.execute("""
        CREATE TABLE cities (
            city TEXT PRIMARY KEY,
            country TEXT,
            iso3 TEXT,                    -- country code for the IMF inflation API (e.g. ESP)
            currency TEXT,
            latitude REAL,
            longitude REAL,
            rent_shared_room REAL,
            rent_dorm REAL,
            rent_apartment REAL,
            groceries_month REAL,
            restaurant_meal REAL,
            evening_out REAL,
            transport_pass REAL,
            price_base_year INTEGER,      -- 2022 = Kaggle prices (adjusted for inflation in the app)
            source TEXT,
            as_of_date TEXT
        )
    """)

    # One city can have several partner universities, so they get their own
    # table. The column city links each university to its row in cities.
    cursor.execute("""
        CREATE TABLE universities (
            university TEXT PRIMARY KEY,
            city TEXT,
            country TEXT,
            reports_in_portal INTEGER,
            last_report_year TEXT,
            study_level TEXT,
            FOREIGN KEY (city) REFERENCES cities(city)
        )
    """)

    cursor.execute("""
        CREATE TABLE experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            housing_type TEXT,
            lifestyle TEXT,
            trips_per_month INTEGER,
            monthly_cost_chf REAL,
            source TEXT,
            FOREIGN KEY (city) REFERENCES cities(city)
        )
    """)


def none_if_missing(value):
    """Empty CSV cells are NaN in pandas. SQLite should store them as NULL (None)."""
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):   # numpy numbers -> normal Python numbers for SQLite
        return value.item()
    return value


def insert_cities(cursor, cities):
    placeholders = ", ".join(["?"] * len(CITY_COLUMNS))  # "?, ?, ?, ...", one per column
    for index, row in cities.iterrows():
        values = [none_if_missing(row[column]) for column in CITY_COLUMNS]
        cursor.execute(
            f"INSERT INTO cities ({', '.join(CITY_COLUMNS)}) VALUES ({placeholders})",
            values,
        )


def insert_universities(cursor, universities):
    for index, row in universities.iterrows():
        cursor.execute(
            """INSERT INTO universities (university, city, country,
                                         reports_in_portal, last_report_year, study_level)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (row["university"], row["city"], row["country"],
             int(none_if_missing(row["reports_in_portal"]) or 0), row["last_report_year"],
             none_if_missing(row["study_level"])),
        )


def insert_experiences(cursor, experiences):
    for index, row in experiences.iterrows():
        cursor.execute(
            """INSERT INTO experiences (city, housing_type, lifestyle, trips_per_month,
                                        monthly_cost_chf, source)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (row["city"], row["housing_type"], row["lifestyle"], int(row["trips_per_month"]),
             float(row["monthly_cost_chf"]), row["source"]),
        )


if __name__ == "__main__":
    # Load the city data
    cities = pd.read_csv(CITIES_CSV)
    print("Loaded", len(cities), "cities from data/cities.csv")

    no_prices = int(cities[PRICE_COLUMNS].isna().all(axis=1).sum())
    incomplete = int(cities[PRICE_COLUMNS].isna().any(axis=1).sum()) - no_prices
    print(no_prices, "cities have no prices at all (NO DATA).")
    print(incomplete, "cities have some prices, but not all.")
    number_of_kaggle_cities = int((cities["price_base_year"] == 2022).sum())
    print(number_of_kaggle_cities, "cities have Kaggle prices (2022, inflation-adjusted in the app).")
    number_of_report_cities = int((cities["price_base_year"] == 2026).sum())
    print(number_of_report_cities, "cities have prices from HSG experience reports.")

    # Load the partner universities
    universities = pd.read_csv(UNIVERSITIES_CSV)
    # Data cleaning: every university must belong to a city we know
    universities = universities[universities["city"].isin(list(cities["city"]))]
    print("Loaded", len(universities), "universities from data/universities.csv")

    # Load (or simulate) the experience data
    if os.path.exists(EXPERIENCES_CSV):
        experiences = pd.read_csv(EXPERIENCES_CSV)
        print("Loaded", len(experiences), "experience rows from data/experiences.csv")
    else:
        experiences = simulate_experiences(cities)
        experiences.to_csv(EXPERIENCES_CSV, index=False)
        print("data/experiences.csv not found -> created", len(experiences), "SIMULATED rows")

    # Data cleaning: only keep experiences for cities we know, with a cost above 0
    known_cities = list(cities["city"])
    experiences = experiences[experiences["city"].isin(known_cities)]
    experiences = experiences[experiences["monthly_cost_chf"] > 0]

    # Write everything into SQLite
    # Delete the old database file, so all tables are built again from the CSV files
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    create_tables(cursor)
    insert_cities(cursor, cities)
    insert_universities(cursor, universities)
    insert_experiences(cursor, experiences)

    connection.commit()
    connection.close()
    print("Saved", len(cities), "cities,", len(universities), "universities and", len(experiences),
          "experiences to", DATABASE_PATH)
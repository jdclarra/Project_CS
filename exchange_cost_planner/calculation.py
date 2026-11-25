"""
Turns the city data (from the database) and the user's inputs into a cost
estimate for the exchange semester:
- monthly costs per category (rent, groceries, restaurants, ...)
- total for the whole stay, with a min-max range
- comparison with the user's own budget

All amounts are in CHF. Conversion into the local currency is done
separately in currency.py.
"""

import pandas as pd

# Settings (agreed with the team, change them here, in one place)

# Which database column holds the rent for each housing type
HOUSING_COLUMNS = {
    "Shared flat room": "rent_shared_room",
    "Student dormitory": "rent_dorm",
    "Own apartment": "rent_apartment",
}

# What each lifestyle means. These are our own assumptions, they are
# shown in the app so that users can see how the estimate is made.
LIFESTYLES = {
    "frugal": {
        "groceries_factor": 0.85,          # cooks at home, buys cheap brands
        "restaurant_meals_per_week": 1,
        "evenings_out_per_month": 2,
    },
    "moderate": {
        "groceries_factor": 1.0,
        "restaurant_meals_per_week": 2,
        "evenings_out_per_month": 4,
    },
    "comfortable": {
        "groceries_factor": 1.15,
        "restaurant_meals_per_week": 4,
        "evenings_out_per_month": 8,
    },
}

WEEKS_PER_MONTH = 4.33       # 52 weeks / 12 months
DAYS_PER_MONTH = 30.44       # 365.25 days / 12 months

# Our estimate is not exact. We show a range of +/- 15 % around it.
UNCERTAINTY = 0.15

COST_PER_TRIP = 150          # average cost of one weekend trip in CHF (travel + hostel)

# The price columns of a city that the calculation needs (amounts in CHF).
# A city without all of them cannot be calculated.
PRICE_COLUMNS = [
    "rent_shared_room",       # per month
    "rent_dorm",              # per month
    "rent_apartment",         # per month
    "groceries_month",        # per month, one person, normal shopping
    "restaurant_meal",        # one meal in an inexpensive restaurant
    "evening_out",            # one evening out (drinks, cinema, ...)
    "transport_pass",         # monthly public transport pass
]

# Helper functions
def value_or_zero(city, column):
    """Return the value of one column, or 0 if it is missing (None / NaN)."""
    value = city.get(column)
    if value is None or pd.isna(value):
        return 0
    return float(value)


def find_missing_values(city):
    """Return a list of required columns that are missing for this city.

    The app should show a warning if this list is not empty, because the
    estimate is then too low.
    """
    missing = []
    for column in PRICE_COLUMNS:
        value = city.get(column)
        if value is None or pd.isna(value):
            missing.append(column)
    return missing


def months_between(start_date, end_date):
    """Length of the stay in months (with decimals), e.g. 4.5 months.

    Both inputs are datetime.date objects, e.g. from st.date_input.
    """
    if end_date <= start_date:
        return 0
    number_of_days = (end_date - start_date).days
    return round(number_of_days / DAYS_PER_MONTH, 1)


# Step 1: monthly costs
def calculate_monthly_costs(city, housing_type, lifestyle, trips_per_month=0):
    """Monthly costs in CHF, per category. Returns a dictionary.

    city            - one row of city data (dict or pandas Series)
    housing_type    - a key of HOUSING_COLUMNS, e.g. "Shared flat room"
    lifestyle       - a key of LIFESTYLES, e.g. "moderate"
    trips_per_month - planned weekend trips per month
    """
    if housing_type not in HOUSING_COLUMNS:
        raise ValueError(f"Unknown housing type: {housing_type}")
    if lifestyle not in LIFESTYLES:
        raise ValueError(f"Unknown lifestyle: {lifestyle}")

    habits = LIFESTYLES[lifestyle]

    rent = value_or_zero(city, HOUSING_COLUMNS[housing_type])
    groceries = value_or_zero(city, "groceries_month") * habits["groceries_factor"]

    # Restaurants and going out: number of times x price of one visit
    restaurants = habits["restaurant_meals_per_week"] * WEEKS_PER_MONTH * value_or_zero(city, "restaurant_meal")
    going_out = habits["evenings_out_per_month"] * value_or_zero(city, "evening_out")

    transport = value_or_zero(city, "transport_pass")
    travel = trips_per_month * COST_PER_TRIP

    monthly_costs = {
        "Rent": rent,
        "Groceries": groceries,
        "Restaurants / going out": restaurants + going_out,
        "Public transport": transport,
        "Leisure / travel": travel,
    }

    # Round every amount to whole francs
    for category in monthly_costs:
        monthly_costs[category] = round(monthly_costs[category])
    return monthly_costs


# Step 2: totals and range
def calculate_totals(monthly_costs, months):
    """Add everything up. Returns a dictionary with the key numbers."""
    monthly_total = sum(monthly_costs.values())
    total = monthly_total * months

    return {
        "monthly_total": round(monthly_total),
        "total": round(total),
        "total_min": round(total * (1 - UNCERTAINTY)),
        "total_max": round(total * (1 + UNCERTAINTY)),
        "months": months,
    }


# Step 3: compare with the user's budget
def compare_with_budget(totals, budget):
    """Compare the estimate with the money the user has (CHF).

    Returns a dictionary with the difference and a short status text:
    "enough", "tight" (budget is inside the range) or "not enough".
    """
    difference = budget - totals["total"]

    if budget >= totals["total_max"]:
        status = "enough"
    elif budget >= totals["total_min"]:
        status = "tight"
    else:
        status = "not enough"

    # How many months the budget lasts
    if totals["monthly_total"] > 0:
        months_covered = budget / totals["monthly_total"]
    else:
        months_covered = 0

    return {
        "budget": budget,
        "difference": round(difference),
        "status": status,
        "months_covered": round(max(0, months_covered), 1),
    }


# Table for the charts in the app
def costs_to_table(monthly_costs, months):
    """Put all costs into one DataFrame - this is the format for the charts.

    Columns: category, chf_per_month, chf_total
    """
    rows = []
    for category, amount in monthly_costs.items():
        rows.append({
            "category": category,
            "chf_per_month": amount,
            "chf_total": round(amount * months),
        })
    return pd.DataFrame(rows)


# Everything in one call - the main function for the app
def estimate_exchange_costs(city, housing_type, lifestyle, months, trips_per_month=0, budget=None):
    """Run steps 1-3 and return all results in one dictionary.

    Keys of the result:
      monthly_costs                  - dictionary per category (CHF)
      monthly_total, total, total_min, total_max, months
      table                          - DataFrame for the charts
      missing_values                 - list of missing city columns (show a warning if not empty)
      budget_check                   - only if a budget was given, otherwise None
    """
    monthly_costs = calculate_monthly_costs(city, housing_type, lifestyle, trips_per_month)
    totals = calculate_totals(monthly_costs, months)

    result = {
        "monthly_costs": monthly_costs,
        "table": costs_to_table(monthly_costs, months),
        "missing_values": find_missing_values(city),
        "budget_check": None,
    }
    result.update(totals)

    if budget is not None and budget > 0:
        result["budget_check"] = compare_with_budget(totals, budget)

    return result

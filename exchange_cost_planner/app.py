"""
app.py - Exchange Cost Planner (Streamlit web application)

Role: "App & Design" - this file builds everything the user sees and
connects the modules of the other roles:

    database.py       SQL queries (cities, universities, experiences)
    calculation.py    rule-based cost estimate
    currency.py       exchange rates (Frankfurter API)
    ml_model.py       our own machine-learning model
    external_data.py  climate (Open-Meteo API) and inflation (IMF API)

Start with:   streamlit run app.py

Pages (chosen in the sidebar):
1. Home / Problem
2. Cost calculator
3. City comparison
4. Weather
5. About the model
"""

import math
from datetime import date

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

import database as db
from calculation import (COST_PER_TRIP, HOUSING_COLUMNS, LIFESTYLES, PRICE_COLUMNS, UNCERTAINTY,
                         estimate_exchange_costs, months_between)
from currency import convert_from_chf, get_exchange_rates
from external_data import get_inflation_factor, get_monthly_climate
from ml_model import predict_monthly_cost, train_models

px.defaults.template = "plotly_white"

# Chart Colors:
CATEGORY_COLORS = {
    "Rent": "#075E45",
    "Groceries": "#57A580",
    "Restaurants / going out": "#A2B874",
    "Public transport": "#217F91",
    "Leisure / travel": "#557B9D",
}
CITY_COLORS = ["#81D8D0", "#187187", "#3A7CA5"]
CHART_MARGIN = {"t": 10, "b": 10, "l": 10, "r": 10}

# Readable names for the price columns of a city
PRICE_LABELS = {
    "rent_shared_room": "Rent shared flat room (per month)",
    "rent_dorm": "Rent student dormitory (per month)",
    "rent_apartment": "Rent own apartment (per month)",
    "groceries_month": "Groceries (per month)",
    "restaurant_meal": "One restaurant meal",
    "evening_out": "One evening out",
    "transport_pass": "Public transport pass (per month)",
}

HOUSING_TYPES = list(HOUSING_COLUMNS.keys())
LIFESTYLE_NAMES = list(LIFESTYLES.keys())

DEFAULT_START = date(2027, 2, 15)
DEFAULT_END = date(2027, 6, 30)
DATE_FORMAT = "DD/MM/YYYY"


# Helper functions:
# Streamlit runs this whole script again after every click.
# Declaration of AI Assistance: the caching pattern with st.session_state was generated with Claude.
# To avoid asking an API every time, successful answers are remembered in st.session_state.
# Failed requests are NOT remembered, so the app tries again next time.

def get_rate_cached(currency_code):
    key = "rates_" + currency_code
    if key in st.session_state:
        return st.session_state[key]

    rates, source = get_exchange_rates([currency_code])
    if rates is not None:
        st.session_state[key] = (rates, source)
    return rates, source


def get_climate_cached(city):
    key = "climate_" + city["city"]
    if key in st.session_state:
        return st.session_state[key]

    climate = get_monthly_climate(city["latitude"], city["longitude"])
    if climate is not None:
        st.session_state[key] = climate
    return climate


def get_inflation_cached(iso3):
    key = "inflation_" + str(iso3)
    if key in st.session_state:
        return st.session_state[key]

    factor = get_inflation_factor(iso3)
    if factor is not None:
        st.session_state[key] = factor
    return factor


# Declaration of AI Assistance: number_of_reports and kaggle_gap_columns were generated with Claude.
# They read information out of the source text in cities.csv by cutting the text with split().
def number_of_reports(city):
    """Number of HSG experience reports behind the prices of a city, 0 if none.

    The number is part of the source text, e.g.
    "HSG experience reports 2023-2026 (n=13 reports, median, CHF; ...)" -> 13
    """
    source = str(city["source"])
    if "(n=" not in source:
        return 0
    text_after = source.split("(n=")[1]     # "13 reports, median, CHF; ..."
    return int(text_after.split(" ")[0])    # "13" -> 13


def kaggle_gap_columns(city):
    """Price columns of a report city that were filled with Kaggle prices from 2022.

    The source text ends with e.g.
    "Gaps filled from Kaggle (..., NOT inflation-adjusted): rent_apartment, groceries_month."
    Only the columns that the calculation uses are returned.
    """
    source = str(city["source"])
    if "NOT inflation-adjusted): " not in source:
        return []
    names = source.split("NOT inflation-adjusted): ")[1].rstrip(".").split(", ")
    columns = []
    for name in names:
        if name in PRICE_COLUMNS:
            columns.append(name)
    return columns


# Declaration of AI Assistance: the inflation adjustment (which prices are from 2022 and get
# multiplied with the IMF factor) was designed and written with Claude.
def load_city_current(city_name):
    """Load a city and adjust prices from 2022 (Kaggle) to today with IMF inflation.

    Kaggle city: all prices are from 2022.
    Report city: the prices from the reports are recent, only the gaps filled from Kaggle are from 2022.
    """
    city = dict(db.load_city(city_name))
    city["inflation_factor"] = 1.0
    if city["price_base_year"] == 2022:
        old_columns = PRICE_COLUMNS
    else:
        old_columns = kaggle_gap_columns(city)

    if len(old_columns) > 0:
        factor = get_inflation_cached(city["iso3"])
        if factor is not None:
            city["inflation_factor"] = factor
            for column in old_columns:
                if pd.notna(city[column]):
                    city[column] = round(city[column] * factor)
    return city


# Declaration of AI Assistance: generated with Claude. The loop compares (year, month) pairs,
# so that a stay over New Year (e.g. September to February) keeps the right order.
def months_of_stay(start_date, end_date):
    """List of the month numbers of the stay in the right order, e.g. [2, 3, 4, 5, 6]."""
    months = []
    year = start_date.year
    month = start_date.month
    while (year, month) <= (end_date.year, end_date.month) and len(months) < 12:
        months.append(month)
        month = month + 1
        if month == 13:  # after December comes January of the next year
            month = 1
            year = year + 1
    return months


def show_price_source(city):
    """Show where the prices of this city come from and how reliable they are."""
    reports = number_of_reports(city)
    if reports > 0:
        st.success(
            f"Prices for **{city['city']}** come from **{reports} HSG experience reports** (2023 to 2026). "
            "For every price we use the median of the values that former exchange students stated."
        )
        if reports < 3:
            st.warning(f"There are only {reports} report(s) for this city, so the prices are not very reliable.")

        # Prices that no report mentions were filled with Kaggle prices from 2022
        gap_names = []
        for column in kaggle_gap_columns(city):
            gap_names.append(PRICE_LABELS[column])
        if len(gap_names) > 0:
            if city["inflation_factor"] == 1.0:
                inflation_text = "not adjusted for inflation, because the IMF API could not be reached"
            else:
                inflation_text = f"adjusted by +{city['inflation_factor'] - 1:.0%} for inflation"
            st.info(
                "No report mentions these prices, so they come from the Kaggle dataset (2022, "
                + inflation_text + "): " + ", ".join(gap_names) + "."
            )

    elif city["price_base_year"] == 2022:
        if city["inflation_factor"] == 1.0:
            st.warning(
                f"Prices for **{city['city']}** are from 2022 (Kaggle). The inflation adjustment "
                "failed because the IMF API could not be reached, so the costs are probably too low."
            )
        else:
            st.info(
                f"Prices for **{city['city']}** come from the Kaggle 'Global Cost of Living' dataset (2022) "
                f"and were adjusted by **+{city['inflation_factor'] - 1:.0%}** for inflation (IMF data)."
            )
        if "Gaps filled from HSG experience reports" in str(city["source"]):
            st.caption("Prices that were missing in the Kaggle dataset were filled with values from HSG experience reports.")


# App setup: check database, load data, train the model:

st.set_page_config(page_title="Exchange Cost Planner", layout="wide")

if not db.database_exists():
    st.error(
        "The database file `database/exchange_costs.db` was not found. "
        "Please run `python create_database.py` in the project folder first."
    )
    st.stop()

city_names = db.load_city_names()
city_names_with_prices = db.load_city_names_with_prices()
all_cities = db.load_all_cities()
all_universities = db.load_universities()

# Text for the university dropdown, e.g. "Keio University - Tokyo, Japan".
# For every label we also remember the city and the study level
# ("Bachelor", "Master", "Both" or empty if unknown).
university_labels = []
city_of_label = {}
level_of_label = {}
for index, row in all_universities.iterrows():
    label = f"{row['university']} - {row['city']}, {row['country']}"
    university_labels.append(label)
    city_of_label[label] = row["city"]
    level_of_label[label] = row["study_level"]
university_labels.sort()

# Train our own ML model on the reported costs every time the app runs.
# This takes well under a second.
training_data = db.load_training_data()
trained = train_models(training_data)  # None if there is not enough data

number_of_simulated_rows = int((training_data["source"] == "simulated").sum())
number_of_cities_without_prices = len(all_cities) - len(city_names_with_prices)

# Cities with prices from HSG experience reports (for the chart on the home page)
report_rows = []
for index, row in all_cities.iterrows():
    if number_of_reports(row) > 0:
        report_rows.append({"city": row["city"], "reports": number_of_reports(row)})
report_table = pd.DataFrame(report_rows)

# Sidebar navigation:

st.sidebar.title("Exchange Cost Planner")
page = st.sidebar.radio(
    "Go to",
    ["Home / Problem", "Cost calculator", "City comparison", "Weather", "About the model"],
)

if number_of_cities_without_prices > 0 or number_of_simulated_rows > 0:
    st.sidebar.warning(
        f"**Data status:** {number_of_cities_without_prices} of {len(all_cities)} cities have no complete prices. "
        f"{number_of_simulated_rows} of {len(training_data)} training rows are simulated."
    )



# PAGE 1: Home / Problem:

if page == "Home / Problem":
    st.title("How much money do I really need for my exchange semester?")
    st.markdown(
        """
        **The problem.** Students who plan an exchange semester often do not know how much money they
        realistically need. Living costs differ a lot between cities, and the information is scattered
        across experience reports, forums and cost-comparison websites. A budget that is too tight, or a
        scholarship or part-time job that is misjudged, can spoil the semester.

        **Who is it for?** Students (first of all at HSG) who choose between several partner universities
        or plan the budget for a destination that is already fixed.

        **What the app does**
        1. **Cost calculator** - choose a city, your dates, housing and lifestyle and get the costs per
           month and for the whole stay, by category, in CHF and in the local currency.
        2. **City comparison** - put two or three cities side by side.
        3. **Weather** - the typical weather during your months abroad.
        4. **About the model** - how our machine-learning model works and how good it is.
        """
    )

    st.subheader("Where you can go")
        # Add the coordinates of the city to every university
    uni_map = all_universities.merge(all_cities[["city", "latitude", "longitude"]], on="city")

        # Declaration of AI Assistance: the world map (merge, groupby with a named aggregation,
        # scatter_map with custom_data and the HTML hover template) was generated with Claude.
        # One row per city with the number of partner universities
    per_city = uni_map.groupby(["city", "country", "latitude", "longitude"], as_index=False).agg(
            universities=("university", "count")
        )

        # Text for the hover box: all partner universities of the city, one per line
    university_lists = []
    for city_name in per_city["city"]:
        names = sorted(uni_map[uni_map["city"] == city_name]["university"])
        text = ""
        for name in names:
            text = text + "<br>• " + name
        university_lists.append(text)
    per_city["university_list"] = university_lists

    fig_world = px.scatter_map(
        per_city,
        lat="latitude",
        lon="longitude",
        size="universities",
        size_max=25,
        hover_name="city",
        custom_data=["country", "universities", "university_list"],
        color_discrete_sequence=["#176B53"],
        zoom=0.6,
        height=450,
        map_style="carto-positron",
    )
    fig_world.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "%{customdata[0]}<br><br>"
            "<b>Partner universities (%{customdata[1]}):</b>"
            "%{customdata[2]}"
            "<extra></extra>"
        )
    )
    
    fig_world.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_color="#20362B",
            align="left"
        ),
        margin=dict(l=0, r=0, t=0, b=0)
    )

    st.plotly_chart(fig_world, width="stretch")

    st.header("Where does the data come from?")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            **SQLite database** (`database/exchange_costs.db`)
            - **Universities**: {len(all_universities)} HSG partner universities and their city
            - **Cities**: {len(all_cities)} cities; {len(city_names_with_prices)} of them have prices so far
              (rent, groceries, restaurants, transport)
            - **Experiences**: {len(training_data)} reported monthly costs - the training data of our model
            """
        )
    with col2:
        st.markdown(
            """
            **Online APIs** (free, no API key)
            - **Frankfurter** - current exchange rates (European Central Bank)
            - **Open-Meteo** - weather of the last three years for the climate chart
            - **IMF Datamapper** - inflation since 2022 used to update database prices to today
            """
        )

    st.warning(
        f"**Data honesty.** The list of partner universities is real (HSG exchange portal). "
        f"{number_of_cities_without_prices} of {len(all_cities)} cities have **no complete prices yet**. "
        f"The prices of {len(report_table)} cities come from HSG experience reports, all others from the "
        f"Kaggle dataset (2022, adjusted for inflation). {number_of_simulated_rows} of {len(training_data)} "
        "training rows are **simulated** and will be replaced by real answers of former exchange students. "
        "All results are estimates, not guarantees."
    )

    st.subheader("Partner universities in the database")
    st.caption("Source: public HSG exchange portal (programme 'Exchange partner university'). "
               "The last columns show how many experience reports the portal lists and from which year the newest is.")
    st.dataframe(all_universities, hide_index=True)

    with st.container(border=True):
        # Chart purpose: see where most partner universities are
        per_country = db.count_universities_per_country().head(15)
        figure = px.bar(
            per_country,
            x="country",
            y="number_of_universities",
            title="Partner universities per country (top 15)",
            labels={"country": "Country", "number_of_universities": "Number of universities"},
        )
        st.plotly_chart(figure, width="stretch")

    st.subheader("Cities and the status of their prices")
    st.dataframe(all_cities[["city", "country", "currency", "source", "as_of_date"]], hide_index=True)


# PAGE 2: Cost calculator:

elif page == "Cost calculator":
    st.title("Cost calculator")

    # Layout agreed in the team: inputs left, results right, breakdown below
    left, right = st.columns([1, 2])

    with left:
        st.subheader("Your plan")
        only_with_prices = st.checkbox("Only universities in cities with prices", value=True)
        study_level = st.radio("Study level", ["All", "Bachelor", "Master"], horizontal=True)
        if only_with_prices:
            shown_labels = [label for label in university_labels if city_of_label[label] in city_names_with_prices]
        else:
            shown_labels = university_labels
        if study_level != "All":
            filtered_labels = []
            for label in shown_labels:
                if level_of_label[label] == study_level or level_of_label[label] == "Both":
                    filtered_labels.append(label)
            shown_labels = filtered_labels

        if len(shown_labels) == 0:
            st.warning("No partner university matches these filters.")
            st.stop()
        university_label = st.selectbox(f"Partner university ({len(shown_labels)})", shown_labels)
        city_name = city_of_label[university_label]
        start_date = st.date_input("Start of stay", value=DEFAULT_START, format=DATE_FORMAT)
        end_date = st.date_input("End of stay", value=DEFAULT_END, format=DATE_FORMAT)
        housing_type = st.selectbox("Housing", HOUSING_TYPES)
        lifestyle = st.radio("Lifestyle", LIFESTYLE_NAMES, index=1, horizontal=True)
        trips_per_month = st.slider("Weekend trips per month", 0, 4, 1)
        budget_type = st.radio("My budget is ...", ["for the whole stay", "per month"], horizontal=True)
        budget = st.number_input(f"My budget in CHF ({budget_type}, optional)",
                                 min_value=0, max_value=100000, value=0, step=100)

    city = load_city_current(city_name)
    months = months_between(start_date, end_date)
    # A monthly budget is converted to a budget for the whole stay, 
    # because the calculation compares the budget with the total costs.
    if budget_type == "per month":
        total_budget = budget * months
    else:
        total_budget = budget

    with right:
        if months == 0:
            st.error("The end date must be after the start date.")
            st.stop()

        if city_name not in city_names_with_prices:
            st.error(
                f"We do not have **all prices for {city_name}** yet, so a cost estimate is not possible. "
                "You can still look at the weather for this city."
            )
            # Show at least the prices we already know from experience reports
            reports = number_of_reports(city)
            if reports > 0:
                st.subheader(f"What {reports} HSG experience report(s) say about {city_name}")
                known_prices = []
                for column in PRICE_COLUMNS:
                    if pd.notna(city[column]):
                        known_prices.append({"price": PRICE_LABELS[column], "chf": round(city[column])})
                st.dataframe(pd.DataFrame(known_prices), hide_index=True)
            st.stop()

        show_price_source(city)

        # Rule-based estimate (calculation.py)
        result = estimate_exchange_costs(
            city, housing_type, lifestyle, months,
            trips_per_month=trips_per_month, budget=total_budget,
        )

        if len(result["missing_values"]) > 0:
            st.warning("Missing data for this city: " + ", ".join(result["missing_values"])
                       + ". The estimate is too low.")

        st.subheader(f"Estimate for {months} months in {city_name}")
        st.caption("Partner universities in this city: " + "; ".join(db.load_universities_in_city(city_name)))

        col1, col2 = st.columns(2, gap="medium")
        with col1:
            with st.container(border=True):
                st.metric("Monthly estimate", f"CHF {result['monthly_total']:,}")
        with col2:
            with st.container(border=True):
                st.metric("Total for your stay", f"CHF {result['total']:,}")

        st.write(
            f"Realistic range: **CHF {result['total_min']:,} - {result['total_max']:,}** "
            f"(monthly costs plus or minus {UNCERTAINTY:.0%}, because this is an estimate)."
        )

        # Local currency (currency.py, Frankfurter API)
        rates, rate_source = get_rate_cached(city["currency"])
        if rates is None:
            st.info("The exchange rate is not available right now - amounts are shown in CHF only.")
        elif city["currency"] != "CHF":
            rate = rates[city["currency"]]
            st.write(
                f"In local currency: about **{convert_from_chf(result['total'], rate):,} {city['currency']}** "
                f"in total, **{convert_from_chf(result['monthly_total'], rate):,} {city['currency']}** per month "
                f"(1 CHF = {rate} {city['currency']}, {rate_source})."
            )

     # Budget check (compared with the total for the whole stay)
        check = result["budget_check"]
        if check is not None:
            st.caption(f"Your budget: CHF {total_budget / months:,.0f} per month = "
                       f"CHF {total_budget:,.0f} for the whole stay ({months} months).")
            if check["status"] == "enough":
                st.success(f"Your budget is enough: about CHF {check['difference']:,} are left over for the whole stay.")
            elif check["status"] == "tight":
                st.warning("Your budget is tight: it lies inside the uncertainty range of the estimate.")
            else:
                st.error(f"Your budget is about CHF {-check['difference']:,} too low for the whole stay. "
                         f"It covers roughly {check['months_covered']} months.")

        # Machine-learning estimate (ml_model.py)
        st.subheader("Second opinion: our machine-learning model")
        if trained is None:
            st.info("There is not enough training data yet to train the model.")
        else:
            ml_monthly = predict_monthly_cost(trained, city, housing_type, lifestyle, trips_per_month)
            col1, col2 = st.columns(2)
            col1.metric("Calculator (prices x quantities)", f"CHF {result['monthly_total']:,} / month")
            col2.metric("Model (learned from reported costs)", f"CHF {ml_monthly:,} / month")
            st.caption(
                f"The model ({trained['model_name']}) was trained on {trained['number_of_rows']} reported monthly "
                f"costs and is off by about CHF {trained['mae']:,.0f} per month on average. "
                f"{number_of_simulated_rows} of these reports are simulated. See 'About the model'."
            )

    # Breakdown below
    st.subheader("Cost breakdown")

    table = result["table"]
    chart_table = table[table["chf_total"] > 0]

    chart_left, chart_right = st.columns(2, gap="medium")

    # Donut chart
    with chart_left:
        with st.container(border=True):
            st.markdown("#### Cost distribution")
            st.caption("See which categories make up most of your budget.")
            fig_donut = px.pie(
                chart_table,
                names="category",
                values="chf_total",
                hole=0.55,
                color="category",
                color_discrete_map=CATEGORY_COLORS,
            )
            # Declaration of AI Assistance: the styling of the donut (white borders, total in the middle
            # as an annotation) was generated with Claude.
            fig_donut.update_traces(textposition="inside", textinfo="percent",
                                    marker={"line": {"color": "white", "width": 2}})
            fig_donut.update_layout(
                annotations=[{"text": f"<b>CHF {result['total']:,}</b><br>total",
                              "showarrow": False, "font": {"size": 18}}],
                margin=CHART_MARGIN,
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_donut, width="stretch")

    # Bar chart
    with chart_right:
        with st.container(border=True):
            st.markdown("#### Costs by category")
            st.caption("See how much each category costs over your stay.")
            fig_bar = px.bar(
                chart_table.sort_values("chf_total"),
                x="chf_total",
                y="category",
                color="category",
                orientation="h",
                color_discrete_map=CATEGORY_COLORS,
                labels={"chf_total": "CHF for the whole stay", "category": ""},
            )
            fig_bar.update_layout(showlegend=False, margin=CHART_MARGIN, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_bar, width="stretch")

    st.subheader("How your money develops over the stay")
    st.caption("Purpose: see when you would run out of budget.")
    # Declaration of AI Assistance: the budget timeline (month steps with math.ceil, area chart and
    # budget line with add_hline) was generated with Claude.
    # Months 0, 1, 2, ... and the exact end of the stay (e.g. 4.4)
    month_steps = list(range(0, math.ceil(months))) + [months]
    spent = []
    for month in month_steps:
        spent.append(result["monthly_total"] * month)
    timeline = pd.DataFrame({"month": month_steps, "spent": spent})
    fig_timeline = px.area(timeline, x="month", y="spent", color_discrete_sequence=["#00802F"],
                           labels={"month": "Month of stay", "spent": "Spent so far (CHF)"})
    if total_budget > 0:
        fig_timeline.add_hline(y=total_budget, line_dash="dash", line_color="#D62828",
                               annotation_text=f"Your budget: CHF {total_budget:,.0f}")
    st.plotly_chart(fig_timeline, width="stretch")

    st.dataframe(table, hide_index=True)

    with st.expander("How is this calculated?"):
        habits = LIFESTYLES[lifestyle]
        st.markdown(
            f"""
            - **Rent:** price for "{housing_type}" in {city_name}.
            - **Groceries:** normal monthly shopping x {habits['groceries_factor']} (lifestyle "{lifestyle}").
            - **Restaurants / going out:** {habits['restaurant_meals_per_week']} restaurant meals per week and
              {habits['evenings_out_per_month']} evenings out per month x the local price.
            - **Public transport:** monthly pass.
            - **Leisure / travel:** {trips_per_month} weekend trips per month x CHF {COST_PER_TRIP}.
            - **Range:** monthly costs plus or minus {UNCERTAINTY:.0%}.
            - Price source for this city: {city['source']} (as of {city['as_of_date']}).
            """
        )


# PAGE 3: City comparison:

elif page == "City comparison":
    st.title("City comparison")
    st.write("Compare two or three cities with the same personal plan.")

    st.caption(f"Only the {len(city_names_with_prices)} cities with prices can be compared.")
    chosen_cities = st.multiselect("Cities (maximum 3)", city_names_with_prices,
                                   default=city_names_with_prices[:2], max_selections=3)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        housing_type = st.selectbox("Housing", HOUSING_TYPES)
    with col2:
        lifestyle = st.selectbox("Lifestyle", LIFESTYLE_NAMES, index=1)
    with col3:
        months = st.slider("Length of stay (months)", 1, 12, 5)
    with col4:
        trips_per_month = st.slider("Weekend trips per month", 0, 4, 1)

    if len(chosen_cities) < 2:
        st.info("Please choose at least two cities.")
        st.stop()

    # Calculate the estimate for every chosen city
    summary_rows = []
    category_tables = []
    for name in chosen_cities:
        city = load_city_current(name)
        result = estimate_exchange_costs(city, housing_type, lifestyle, months, trips_per_month=trips_per_month)

        summary = {
            "city": name,
            "per_month_chf": result["monthly_total"],
            "total_chf": result["total"],
            "hsg_reports": number_of_reports(city),
        }
        if trained is not None:
            summary["ml_model_per_month_chf"] = predict_monthly_cost(trained, city, housing_type, lifestyle, trips_per_month)
        summary_rows.append(summary)

        city_table = result["table"].copy()
        city_table["city"] = name
        category_tables.append(city_table)

    # Declaration of AI Assistance: stacking the category tables of all cities with pd.concat
    # for the stacked bar chart was generated with Claude.
    summary_table = pd.DataFrame(summary_rows).sort_values("total_chf")
    all_categories = pd.concat(category_tables)  # stack the tables of all cities

    cheapest = summary_table.iloc[0]
    most_expensive = summary_table.iloc[-1]
    st.success(
        f"**{cheapest['city']}** is the cheapest of your cities: CHF {cheapest['total_chf']:,} in total, "
        f"CHF {most_expensive['total_chf'] - cheapest['total_chf']:,} less than {most_expensive['city']}."
    )

    st.subheader("Total cost of the stay")
    with st.container(border=True):
        st.markdown("#### Total cost comparison")
        st.caption("Compare your estimated total costs across cities.")
        fig_total = px.bar(
            summary_table,
            x="city",
            y="total_chf",
            text="total_chf",
            color="city",
            color_discrete_sequence=CITY_COLORS,
            labels={"city": "", "total_chf": "Total (CHF)"},
        )
        fig_total.update_traces(texttemplate="CHF %{text:,}", textposition="outside")
        fig_total.update_layout(showlegend=False, margin={"t": 30, "b": 10, "l": 10, "r": 10},
                                paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_total, width="stretch")

    st.subheader("Costs per category")
    with st.container(border=True):
        st.markdown("#### Cost structure by city")
        st.caption("See where the differences between cities come from.")
        fig_categories = px.bar(
            all_categories[all_categories["chf_total"] > 0],
            x="chf_total",
            y="city",
            color="category",
            orientation="h",
            color_discrete_map=CATEGORY_COLORS,
            labels={"chf_total": "CHF for the whole stay", "city": "", "category": ""},
        )
        fig_categories.update_layout(barmode="stack", height=150 + 80 * len(chosen_cities),
                                     margin=CHART_MARGIN, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_categories, width="stretch")

    st.dataframe(summary_table, hide_index=True)


# PAGE 4: Weather:

elif page == "Weather":
    st.title("Weather")

    col1, col2, col3 = st.columns(3)
    with col1:
        city_name = st.selectbox("City", city_names)
    with col2:
        start_date = st.date_input("Start of stay", value=DEFAULT_START, format=DATE_FORMAT)
    with col3:
        end_date = st.date_input("End of stay", value=DEFAULT_END, format=DATE_FORMAT)

    if end_date <= start_date:
        st.error("The end date must be after the start date.")
        st.stop()

    city = db.load_city(city_name)
    st.caption("Partner universities in this city: " + "; ".join(db.load_universities_in_city(city_name)))

    # Climate (Open-Meteo API)
    st.header("Typical weather during your stay")
    with st.spinner("Loading weather data from Open-Meteo ..."):
        climate = get_climate_cached(city)

    if climate is None:
        st.warning("The weather service could not be reached. Please try again later.")
    else:
        # Keep only the months of the stay, in the order of the stay (e.g. Sep, Oct, Nov, Dec, Jan)
        # Declaration of AI Assistance: filtering and sorting the climate data in the order of the stay
        # was generated with Claude.
        stay_months = months_of_stay(start_date, end_date)
        stay_climate = climate[climate["month"].isin(stay_months)].copy()
        stay_climate["order"] = [stay_months.index(month) for month in stay_climate["month"]]
        stay_climate = stay_climate.sort_values("order")

        st.caption(
            "These are climate averages of the last three years, not a forecast - "
            "nobody can forecast the weather several months ahead."
        )
        col1, col2 = st.columns(2)
        col1.metric("Average temperature", f"{stay_climate['temperature_c'].mean():.1f} °C")
        col2.metric("Rain per month", f"{stay_climate['rain_mm'].mean():.0f} mm")

        with st.container(border=True):
            st.markdown("#### Temperature & rainfall")
            st.caption("Explore the typical weather during your stay.")

            # Declaration of AI Assistance: the chart with two y-axes (make_subplots, go.Bar, go.Scatter,
            # secondary_y) was generated with Claude.
            # One chart with two y-axes: rain as bars (left), temperature as a line (right)
            fig_climate = make_subplots(specs=[[{"secondary_y": True}]])
            fig_climate.add_trace(
                go.Bar(x=stay_climate["month_name"], y=stay_climate["rain_mm"],
                       name="Rain (mm)", marker_color="#83B7C3"),
                secondary_y=False,
            )
            fig_climate.add_trace(
                go.Scatter(x=stay_climate["month_name"], y=stay_climate["temperature_c"],
                           name="Temperature (°C)", mode="lines+markers",
                           line={"color": "#176B53", "width": 3}),
                secondary_y=True,
            )
            fig_climate.update_yaxes(title_text="Rain (mm per month)", secondary_y=False)
            fig_climate.update_yaxes(title_text="Mean temperature (°C)", secondary_y=True)
            fig_climate.update_layout(
                template="plotly_white",
                legend={"orientation": "h", "y": 1.15},
                margin={"t": 55, "b": 10, "l": 10, "r": 10},
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_climate, width="stretch")


# PAGE 5: About the model:

elif page == "About the model":
    st.title("About the model")

    if trained is None:
        st.info("There is not enough training data yet to train the model.")
        st.stop()

    st.markdown(
        f"""
        - **What it predicts:** the total living cost of one exchange student per month, in CHF.
        - **Inputs:** prices of the city (rent for the chosen housing, groceries, restaurant meal, evening out,
          transport pass) and the personal plan (housing type, lifestyle, weekend trips per month).
          Text inputs are turned into 0/1 columns (one-hot encoding).
        - **Training data:** {trained['number_of_rows']} monthly costs reported by former exchange students,
          loaded from our database. 80 % are used for training, 20 % are kept aside for testing.
        - **Two models compared:** a linear regression and a random forest (100 decision trees).
          We use the one with the smaller error; if they are similar we keep the linear regression because it
          is easier to explain. **Chosen: {trained['model_name']}.**
        """
    )

    if number_of_simulated_rows > 0:
        st.warning(
            f"{number_of_simulated_rows} of the {trained['number_of_rows']} training rows are **simulated** "
            "(created by `create_database.py` from our cost calculator plus random noise). Until they are "
            "replaced by real survey answers, the model mostly re-learns our own calculator."
        )

    st.subheader("How good is it?")
    col1, col2 = st.columns(2)
    col1.metric("MAE linear regression", f"CHF {trained['mae_linear']:,.0f}")
    col2.metric("MAE random forest", f"CHF {trained['mae_forest']:,.0f}")
    st.write(
        "**MAE** means *mean absolute error*: for every test student we take the difference between the "
        "predicted and the real monthly cost, ignore the sign, and average these differences. "
        f"An MAE of CHF {trained['mae']:,.0f} means the model is off by about that much per month on average. "
        f"The average reported cost is CHF {training_data['monthly_cost_chf'].mean():,.0f} per month."
    )

    chart_left, chart_right = st.columns(2, gap="medium")

    with chart_left:
        with st.container(border=True):
            st.markdown("#### Predicted vs. actual costs")
            st.caption("Points closer to the diagonal indicate better predictions.")
            test_results = trained["test_results"]
            fig_test = px.scatter(
                test_results,
                x="actual_cost",
                y="predicted_cost",
                labels={"actual_cost": "Reported cost (CHF)", "predicted_cost": "Predicted cost (CHF)"},
                color_discrete_sequence=["#176B53"],
            )
            # Declaration of AI Assistance: the diagonal reference line (add_shape) was generated with Claude.
            # Diagonal line: on this line the prediction is exactly right
            highest = test_results["actual_cost"].max()
            fig_test.add_shape(type="line", x0=0, y0=0, x1=highest, y1=highest,
                               line={"dash": "dash", "color": "#8FA99B"})
            fig_test.update_layout(margin=CHART_MARGIN, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_test, width="stretch")

    with chart_right:
        with st.container(border=True):
            st.markdown("#### Reported costs by city")
            st.caption("Average monthly costs based on training data.")
            reported = db.average_reported_cost_per_city()
            fig_reported = px.bar(
                reported.sort_values("average_monthly_cost_chf"),
                x="average_monthly_cost_chf",
                y="city",
                orientation="h",
                hover_data=["number_of_reports"],
                color_discrete_sequence=["#4F9679"],
                labels={"average_monthly_cost_chf": "Average reported cost (CHF per month)", "city": ""},
            )
            fig_reported.update_layout(margin=CHART_MARGIN, paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_reported, width="stretch")

    if trained["model_name"] == "Linear regression":
        st.subheader("What the model learned")
        st.caption("Coefficient = change of the predicted monthly cost (CHF) when the input goes up by 1.")
        # Declaration of AI Assistance: reading the learned coefficients of the linear regression
        # (model.coef_) was generated with Claude.
        coefficients = pd.DataFrame({
            "input": trained["feature_columns"],
            "coefficient": trained["model"].coef_.round(2),
        })
        st.dataframe(coefficients, hide_index=True)

    st.subheader("Where the training data comes from")
    st.dataframe(db.count_training_rows_by_source(), hide_index=True)

    st.subheader("Limitations")
    st.markdown(
        """
        - The model can only be as good as its data. With simulated or very few reports it is not reliable.
        - It knows nothing about things that are not in the data, e.g. the exact neighbourhood, inflation,
          exchange-rate changes or personal habits.
        """
    )

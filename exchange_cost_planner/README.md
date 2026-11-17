# Exchange Cost Planner

A Streamlit web app for the group project in *Fundamentals and Methods of Computer Science for Business
Studies* (University of St. Gallen, HSG).

## 1. Problem statement

Students who plan an exchange semester often do not know how much money they realistically need. Living
costs differ a lot between cities, and the information is scattered across experience reports, forums
and cost-comparison websites. Missing and hard-to-compare cost information leads to poor planning: a
budget that is too tight, or a scholarship or part-time job that is misjudged.

The Exchange Cost Planner gives a **personal cost estimate for the whole stay** in a chosen city, broken
down by category, and also shows the typical weather during the semester.

## 2. Target group

Students (first of all at HSG) who choose between several partner universities or plan their budget for
a destination that is already fixed.

## 3. Features

| Page | What the user can do |
|------|----------------------|
| **Home / Problem** | Read the problem, see all partner universities on a world map and where the data comes from |
| **Cost calculator** | Filter the partner universities by study level (Bachelor / Master), choose a university, dates, housing, lifestyle, weekend trips and an optional budget → costs per month, total, realistic range, local currency, budget check, estimate of our ML model, charts and a cost table |
| **City comparison** | Compare 2 or 3 cities with the same plan → cheapest city, total-cost chart, costs per category, table |
| **Weather** | Typical temperature and rain for the months of the stay |
| **About the model** | What the model predicts, training data, error of both models, charts, limitations |

## 4. Data sources and what is real

| Data | Where | Status |
|------|-------|--------|
| Partner universities (`data/universities.csv` → table `universities`) | HSG Mobility-Online portal and the HSG list of partner universities | **Real**: 222 entries in 134 cities and 53 countries. The column `study_level` (Bachelor / Master / Both) comes from the HSG list of partner universities; it is empty for 24 entries that offer no regular Bachelor or Master exchange there |
| Cities and prices (`data/cities.csv` → table `cities`) | Kaggle "Global Cost of Living" (Numbeo, Dec 2022), HSG experience reports | Cities, countries, currencies are real. **102 cities** have prices from the Kaggle dataset (2022); the app adjusts them for inflation with the IMF API. **15 cities** have **mostly PLACEHOLDER prices** (some single values come from HSG experience reports). **17 cities** have no complete prices yet. The app warns about this on every page that uses them. |
| Reported monthly costs (`data/experiences.csv` → table `experiences`) | survey + HSG experience reports | **300 SIMULATED rows** (created by `create_database.py` from our cost calculator plus random noise, `source = "simulated"`) + **13 real rows** from HSG experience reports (`source = "experience report"`, numbers only) |
| Exchange rates | Frankfurter API (European Central Bank) | real, live |
| Climate | Open-Meteo archive API | real, live (average of the last 3 complete years) |
| Inflation since 2022 | IMF DataMapper API | real, live |

Details, dates and licence notes: see [DATA_SOURCES.md](DATA_SOURCES.md).

## 5. Machine learning

- **Goal:** predict the monthly living cost (CHF) of one exchange student.
- **Training data:** reported monthly costs (table `experiences`), joined with the prices
  of the city (SQL `JOIN` in `database.py → load_training_data()`).
- **Features:** rent for the chosen housing type, groceries, restaurant meal, evening out, transport pass,
  weekend trips per month, plus 0/1 columns for lifestyle and housing type (`pd.get_dummies`).
- **Models:** `LinearRegression` and `RandomForestRegressor` (100 trees), both trained by us with
  `model.fit(...)` in `ml_model.py → train_models()` after a `train_test_split` (80 % / 20 %).
- **Comparison:** mean absolute error (MAE) in CHF. The random forest is only used if its error is at
  least 10 % smaller; otherwise we keep the linear regression because it is easier to explain.
- **Current result (300 simulated + 13 real rows):** linear regression MAE ≈ CHF 170 per month, random forest ≈ CHF 212
  → the **linear regression** is used. The average reported cost is about CHF 2,014 per month.
- The app shows the rule-based estimate and the model's estimate side by side.

**Honest limitation:** as long as the training data is simulated from our own calculator, the model
mostly re-learns the calculator. It becomes meaningful with real survey answers.

## 6. Installation

Python 3.10 or newer.

```bash
cd exchange_cost_planner
pip install -r requirements.txt
```

On a Mac use `python3 -m pip install -r requirements.txt`.

## 7. How to run

```bash
python create_database.py     # only needed after changing the CSV files
streamlit run app.py
```

On a Mac: `python3 create_database.py` and `python3 -m streamlit run app.py`.
The browser opens at <http://localhost:8501>. Stop the app with Ctrl + C.

Check the calculations: `python check_calculation.py` (must end with "All 26 checks passed.").

## 8. File structure and who owns which file

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
├── data/experiences.csv   # reported monthly costs (300 simulated + 13 from experience reports)
├── data/last_rates.json   # last exchange rates, used when the Frankfurter API cannot be reached
├── database/exchange_costs.db
├── requirements.txt
├── README.md              # this file
├── SCHNITTSTELLEN.md      # interfaces between the modules (German)
├── DATA_SOURCES.md        # sources, dates, real / placeholder / simulated
├── CONTRIBUTIONS.md       # contribution matrix (TEMPLATE)
├── AI_USAGE.md            # how GenAI was used
├── VIDEO_PLAN.md          # plan for the 4-minute video
├── TEST_CHECKLIST.md      # manual tests
└── REQUIREMENTS_AUDIT.md  # check against the 8 course requirements
```

## 9. Dependencies

| Package | Why |
|---------|-----|
| `streamlit` | the web interface |
| `pandas` | tables, reading SQL results, grouping |
| `numpy` | random numbers for the simulated data |
| `scikit-learn` | `LinearRegression`, `RandomForestRegressor`, `train_test_split`, `mean_absolute_error` |
| `plotly` | charts and the map |
| `requests` | HTTP requests to the three APIs (Frankfurter, Open-Meteo, IMF) |
| `sqlite3`, `json`, `math`, `datetime` | built into Python |

## 10. Limitations

- Most prices are from 2022 and only adjusted with the general inflation of the country. 15 cities still have placeholder prices, and 300 of 313 training rows are simulated until the team replaces them.
- Costs depend on things the app does not know: exact neighbourhood, personal habits.
- The app only estimates the monthly living costs. One-time costs such as flights, visa, deposit or insurance are not included.
- The exchange rate is today's rate; it can change before and during the stay.
- The climate chart shows averages of three past years, not a forecast.
- All results are estimates and not financial advice.

## 11. AI-use note

Generative AI (Claude, by Anthropic) generated the initial implementation of the code and the
documentation. Every Python file is marked with an `# AI assistance:` comment at the top. See
[AI_USAGE.md](AI_USAGE.md); the team must complete it so that it reflects the real use.

## 12. Mapping to the course requirements

**Requirement 1 – Clear problem**
How fulfilled: sections 1–2 of this README and the page *Home / Problem* (budget planning for an exchange semester).

**Requirement 2 – API / database**
How fulfilled: SQLite database with three tables, built with CREATE TABLE and INSERT in `create_database.py` and queried in `database.py` (SELECT, WHERE with `?`, ORDER BY, JOIN, GROUP BY). Three APIs: Frankfurter (`currency.py`), Open-Meteo and IMF DataMapper (`external_data.py`).

**Requirement 3 – Visualisation**
How fulfilled: world map of the partner universities, partner universities per country, donut and bar chart of the cost categories, budget timeline, total-cost and per-category comparison charts, temperature and rain chart, predicted-vs-real scatter, reported cost per city. Each chart states its purpose.

**Requirement 4 – User interaction**
How fulfilled: study level filter, inputs for university, dates, housing, lifestyle, trips and budget; city multiselect for the comparison; city and dates on the weather page.

**Requirement 5 – Own machine-learning model**
How fulfilled: `ml_model.py → train_models()` trains a linear regression and a random forest with `model.fit(...)` on our database, compares them with MAE, and `predict_monthly_cost()` is used in the calculator and the comparison.

**Requirement 6 – Documented code**
How fulfilled: a header docstring in every file; comments on SQL, API requests, data cleaning, feature creation, training, prediction and the purpose of each chart.

**Requirement 7 – Contributions and GenAI**
How fulfilled: `CONTRIBUTIONS.md` (matrix template), `AI_USAGE.md`, `# AI assistance:` comments. Both are part of the video plan. The team must fill them in.

**Requirement 8 – Video**
How fulfilled: `VIDEO_PLAN.md` gives a timed plan for a video of at most 4 minutes with the students' own voice-over.

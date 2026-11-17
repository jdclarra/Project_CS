# Manual test checklist – Exchange Cost Planner

Tick each box after testing. Tester: ________ Date: ________

## Setup

- [ ] Fresh copy of the folder: `pip install -r requirements.txt` finishes without errors
- [ ] `python check_calculation.py` ends with "All 26 checks passed."
- [ ] `python create_database.py` prints "Saved 134 cities, 222 universities and 313 experiences …"
- [ ] `streamlit run app.py` opens the app without an error
- [ ] `python currency.py` (with internet) prints example rates marked "live"

## Home / Problem

- [ ] Problem, target group and data sources are shown
- [ ] The data-honesty warning shows the number of placeholder cities and simulated rows
- [ ] The world map shows the partner universities when you move the mouse over a city
- [ ] The city table lists all cities

## Cost calculator

- [ ] Study level "Bachelor" or "Master" makes the list of universities shorter; "All" shows all again
- [ ] Changing the university changes all numbers
- [ ] "Own apartment" costs more than "Student dormitory"; "comfortable" costs more than "frugal"
- [ ] More weekend trips increase the total
- [ ] A longer stay increases the total; end date before start date shows an error (no crash)
- [ ] With internet: the amount in local currency and "live (ECB, date)" are shown
- [ ] Budget far above the total → green message; far below → red message with months covered
- [ ] The model estimate is shown next to the calculator estimate
- [ ] Donut chart, bar chart, budget timeline and cost table are shown; "How is this calculated?" opens
- [ ] A Kaggle city with internet shows "adjusted by +…% for inflation (IMF data)"
- [ ] A city with placeholder prices shows the yellow placeholder warning

## City comparison

- [ ] With one city: "Please choose at least two cities."
- [ ] With two or three cities: cheapest city message, two charts and the table
- [ ] A fourth city cannot be selected

## Weather

- [ ] With internet: temperature and rain charts show only the months of the stay, in the right order
      (test a stay from September to January)
- [ ] A city in the southern hemisphere (Sydney) is warm in January
- [ ] **API failure:** turn off Wi-Fi → yellow warnings, no crash

## About the model

- [ ] Both MAE values, the scatter chart and the per-city chart are shown
- [ ] The warning about simulated training rows is shown (until real data is in)
- [ ] The coefficient table is shown when the linear regression is used

## Error cases

- [ ] Rename `database/exchange_costs.db` → the app shows "database file … was not found" (rename it back)
- [ ] Empty one price cell in `data/cities.csv`, run `create_database.py` → the calculator warns
      "Missing data for this city" (restore the value afterwards)
- [ ] The app can be stopped (Ctrl + C) and started again

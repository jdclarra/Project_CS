# Data sources – Exchange Cost Planner

This file documents every data source: what it is, when it was collected, and whether it is real,
a placeholder or simulated. **Keep it up to date whenever data is replaced.**

## Overview

| Data | File / table | Status today | To do |
|------|--------------|--------------|-------|
| Partner universities | `data/universities.csv` → `universities` | **Real**: 222 entries in 134 cities (HSG Mobility-Online portal, 2026-11-16, later extended by the team) | Check once a year |
| Study level of the partner universities | column `study_level` in `data/universities.csv` | **Real**: taken from the HSG list of partner universities (Bachelor / Master columns), 2026-11-17 | Check once a year |
| Cities (country, currency, coordinates) | `data/cities.csv` → `cities` | **Real** for 134 cities; coordinates are approximate city centres | – |
| City prices | `data/cities.csv` → `cities` | **23 cities** have prices from **226 HSG experience reports** 2023 to 2026 (`source` starts with `HSG experience reports`, `price_base_year = 2026`); 14 of them are complete, gaps were filled from Kaggle. **106 cities** have prices from the Kaggle "Global Cost of Living" dataset (Numbeo, Dec 2022, `price_base_year = 2022`); 104 of them are complete, 3 have gaps filled from the reports. **5 cities** have no data at all (`NO DATA`). In total **118 cities** have complete prices, **16** do not | Research the missing prices |

**Prices from HSG experience reports (2026-11-17):** for each price the team took the **median** of the
values stated in the reports. The `source` text says how many reports were used in total (`n=… reports`)
and per price (e.g. `rent_dorm n=18`), which prices were filled from Kaggle
(`Gaps filled from Kaggle (…, NOT inflation-adjusted): …`) and whether there are fewer than 3 reports
(`LOW DATA (n<3)`). The app reads the total number of reports, the number of reports per price and the
list of Kaggle gaps from this text, so please keep this format when you add cities. In all 14 complete
report cities at least one price is based on only one or two reports; the app warns about these prices.
| Reported monthly costs | `data/experiences.csv` → `experiences` | **300 simulated rows** (`source = "simulated"`) + **13 real rows** (`source = "experience report"`) | Add the monthly costs from the experience reports |
| Exchange rates | Frankfurter API | Real, live | – |
| Climate | Open-Meteo archive API | Real, live | – |
| US inflation since 2022 | IMF DataMapper API | Real, live; used to bring the Kaggle prices (in US dollars) to today | – |

**Study level (`study_level`):** `Both`, `Bachelor` or `Master`, taken from the Bachelor and Master columns
of the HSG list of partner universities. The column is empty for 24 entries: 18 of them only offer
CEMS, double degree, THEMIS or PhD places there, and 6 are not on the list (Salzburg, USP Instituto de
Relações Internacionais, Duke Fuqua, HSG Latam Term, HSG Asia Term). For Universidad Adolfo Ibañez the
list only names the campus Viña del Mar; the same value is used for the campus Santiago.

## 1. Partner universities and cities

### `data/universities.csv` (222 rows)

| Column | Meaning |
|--------|---------|
| `university` | official name of the partner institution as written in the portal |
| `city` | the city we use in the app; links to `data/cities.csv` |
| `country` | country as written in the portal (Hong Kong: `China (Hong Kong SAR)`) |
| `portal_location` | the place name exactly as in the portal (e.g. `Frederiksberg`, `Cergy-Pontoise Cedex`) |
| `reports_in_portal`, `last_report_year` | how many experience reports the portal lists and the newest academic year |
| `study_level` | `Bachelor`, `Master` or `Both`; empty if unknown (see the overview above) |

**Source and status: real.** One search in the public HSG Mobility-Online portal on 2026-11-16
(experience reports, outgoing students, programme "Exchange partner university";
`registration.exchange.unisg.ch/mobility/MobilitySearchServlet`). It returned 4,973 reports of 184
institutions in 48 countries. Only institution, place, country, year and number of reports were kept.

Things to know:

- The list contains every institution that has **at least one experience report since 2016/2017**.
  Some partnerships may have ended (for example the Russian universities: last report 2021/2022). The
  column `last_report_year` shows this. A brand-new partner without any report is missing.
- Other programmes in the portal (CEMS, double degrees, Freemover, Swiss Mobility, Themis) are not
  included. The portal has 395 institutions over all programmes.
- Some entries are faculties of the same university, and two are HSG's own terms abroad (Asia Term in
  Singapore, Latam Term in Brazil).
- **Our own mapping to a city:** suburbs and campus towns are assigned to the nearby big city, because
  prices and weather are collected per city (e.g. Frederiksberg → Copenhagen, Cergy-Pontoise and
  Jouy-en-Josas → Paris, Sant Cugat → Barcelona, Espoo → Helsinki, Evanston → Chicago, Malibu → Los
  Angeles, Babson Park and Waltham → Boston). The original place stays in `portal_location`.
- For five entries the portal shows no place. We set it ourselves: FGV-EESP → São Paulo, Maastricht
  University (Arts and Social Sciences) → Maastricht, HSG Asia Term → Singapore, International
  University of Japan → Minamiuonuma, HSG Latam Term → São Paulo (**please check this one**).
- Universidad Adolfo Ibañez has two campuses in the portal (Santiago and Viña del Mar), so it has two
  rows.

### `data/cities.csv` (134 rows)

One row per city. **All amounts in CHF.** Columns:

| Column | Meaning |
|--------|---------|
| `city`, `country` | city and country |
| `currency` | local currency (ISO code), only used for display |
| `iso3` | three-letter country code. Not used by the app any more (the app uses the US inflation for all Kaggle prices), so it is not copied into the database |
| `latitude`, `longitude` | position of the city (for the map and the weather) |
| `rent_shared_room`, `rent_dorm`, `rent_apartment` | rent per month |
| `groceries_month` | groceries for one person per month |
| `restaurant_meal` | one meal in an inexpensive restaurant |
| `evening_out` | one evening out (drinks, cinema …) |
| `transport_pass` | monthly public transport pass |
| `price_base_year` | `2022` for Kaggle prices (the app adjusts them for US inflation), `2026` for prices from HSG experience reports |
| `source` | where the prices come from (Kaggle, HSG experience reports with the number of reports, or `NO DATA`) |
| `as_of_date` | date of the data |
| `leisure_month`, `utilities_month`, `kaggle_data_quality` | extra Kaggle values. They stay in the CSV, but the app does not use them, so they are not copied into the database |

**Current status (2026-11-26):**

- **City, country, currency – real.** The currency follows from the country. Not every currency is
  offered by the Frankfurter API; for those the app shows CHF only.
- **Coordinates – approximate city-centre coordinates**, entered by hand (the portal has no
  coordinates). They are only used for the map and the climate.
- **106 cities have prices from the Kaggle dataset** (Numbeo, Dec 2022, converted from USD to CHF).
  `price_base_year = 2022`. The app multiplies them with the **US inflation** since 2022 (IMF API),
  because the Kaggle prices are in US dollars. The inflation of the country itself would be wrong: in
  countries with very high inflation (e.g. Argentina, Venezuela) the local currency loses value at the
  same time, so prices in dollars rise much less.
- **23 cities have prices from HSG experience reports** (see the overview above).
- **16 cities have no complete prices** (5 of them no data at all). We did not invent numbers for them.
  In the app these cities work on the weather page, but the cost calculator says that no estimate is
  possible (and shows the prices that are known) and the comparison only offers cities with prices.
- There are **no placeholder prices** any more.

**Older version, kept for reference: prices taken from HSG experience reports** (4 most recent reports per university were read, 60 in
total, of which 54 are different documents; `n` = number of reports that state the value; with several
values we use the median; ranges are replaced by their midpoint):

| City | Column | Stated in the reports | CHF |
|------|--------|-----------------------|-----|
| Milan | `rent_shared_room` | EUR 1,000 and 1,050 (n=2) | 950 |
| Milan | `rent_dorm` | EUR 5,600 for a 5-month term (n=1) | 1040 |
| Milan | `transport_pass` | EUR 22 student pass (n=3) | 20 |
| Paris | `rent_dorm` | EUR 600, HEC campus residence (n=3) | 560 |
| Copenhagen | `rent_dorm` | CHF 950, CBS housing (n=1) | 950 |
| Copenhagen | `transport_pass` | CHF 70 for 30 days (n=1) | 70 |
| Stockholm | `transport_pass` | SEK 650 and 680, student pass (n=2) | 55 |
| Rotterdam | `rent_shared_room` | EUR 780 (n=1) | 720 |
| Rotterdam | `rent_apartment` | EUR 1,300, studio (n=1) | 1200 |
| Barcelona | `rent_shared_room` | EUR 800–850 (n=1) | 760 |
| Barcelona | `transport_pass` | T-jove EUR 40–44 for 3 months (n=2) | 13 |
| Lisbon | `rent_shared_room` | EUR 950 and 1,000 (1 report, 2 rooms) | 900 |
| Lisbon | `transport_pass` | EUR 40 (n=1) | 37 |
| Vienna | `rent_shared_room` | EUR 650 (n=1) | 600 |
| Vienna | `rent_dorm` | EUR 745, studio in a student residence (n=1) | 690 |
| Vienna | `transport_pass` | EUR 60 and 65.20 (n=2) | 58 |
| London | `rent_shared_room` | GBP 1,400 / 1,400 / 1,500 (n=3) | 1550 |
| Singapore | `rent_shared_room` | SGD 1,650, co-living (n=1) | 1070 |
| Hong Kong | `rent_shared_room` | CHF 1,500 (n=1) | 1500 |
| Tokyo | `rent_dorm` | JPY 75,000, Keio dormitory (n=1) | 390 |
| Tokyo | `transport_pass` | about CHF 150 train fares per month, no pass (n=1) | 150 |
| Sydney | `rent_shared_room` | AUD 1,900 and CHF 1,000 (n=2) | 1040 |
| Austin | `rent_shared_room` | USD 1,000 and 1,250 (n=2) | 940 |

Vancouver: no usable price found in the 4 reports.

**Conversion to CHF:** Frankfurter API (ECB reference rates) of 2026-11-13, 1 CHF = 1.0792 EUR,
8.0678 DKK, 11.9874 SEK, 0.90178 GBP, 1.5364 SGD, 190.84 JPY, 1.7578 AUD, 1.1927 USD. Rents are rounded
to CHF 10. The reports are from 2024–2026, so the rate at the time of the stay was slightly different.

**Limits of these numbers:** one to three reports per value is a very small sample, the reports are an
unofficial source ("subject to change", as the portal says), and what one student paid is not the
average price in the city.

**How to replace them:**
1. For each city, look up the values (suggested sources below) and convert them to CHF.
2. Write the source and date into `source` and `as_of_date` (e.g. `"CBS housing page + Numbeo, CHF rate 0.12"`).
3. Leave a cell empty if a value cannot be found. The app then warns that the estimate is too low.
4. Run `python create_database.py`.

**Suggested sources (to be checked by the team):**
- cost-of-living pages of the partner universities (many publish a monthly budget for exchange students)
- student housing offices and dormitory price lists
- public transport operators (monthly student pass)
- the public HSG experience reports

**Not allowed / to be careful with:** Numbeo's API is paid, and its website terms do not allow copying
the data in bulk or scraping it. Looking up single values by hand and citing the source is the safe way.
A Kaggle dataset that was scraped from Numbeo has the same problem; ask the tutor before using one.

## 2. Reported monthly costs (`data/experiences.csv`)

Columns: `city, housing_type, lifestyle, trips_per_month, monthly_cost_chf, source`.

- `housing_type` must be one of: `Shared flat room`, `Student dormitory`, `Own apartment`
- `lifestyle` must be one of: `frugal`, `moderate`, `comfortable`
- `city` must exist in `data/cities.csv`

**Current status: 300 simulated rows + 13 real rows.**

*Simulated (`source = "simulated"`).* If the file does not exist, `create_database.py` creates 300
fictional rows: random city, housing, lifestyle and trips; the monthly cost is the result of our own
calculator (`calculation.py`) multiplied by random noise of about ±12 % (fixed random seed 2026, so
everyone gets the same file). They were created again on 2026-11-16 after `cities.csv` changed. The app
shows how many training rows are simulated.

*Real (`source = "experience report"`).* 13 rows from the same 60 HSG experience reports (2024/2025 and
2025/2026). Rules we used:

- Only **numbers** were taken: city, housing type and the stated monthly cost. No text was copied and
  no names are stored. The downloaded reports are not part of this repository.
- A row was only created if a report states a **total monthly cost including rent** (or rent plus the
  monthly cost without rent) **and** the housing type is clear. Some of these numbers are the budget
  the author recommends, not an exact record of spending.
- Not used: totals that include the flights to the country or are mainly travel, totals without a
  clear housing type, and reports that only state the rent. Identical reports uploaded by two students
  count once.
- Ranges are replaced by their midpoint, foreign currencies converted with the rates above, result
  rounded to CHF 10.
- **Assumptions, because the reports do not state them:** `lifestyle` is always `moderate`;
  `trips_per_month` is `1`, or `0` if the report says the amount is "excluding travel".

Rows per city: Paris 2, Rotterdam 2, and one each for Copenhagen, Barcelona, Milan, London, Singapore,
Hong Kong, Tokyo, Sydney and Austin. With 13 real rows against 300 simulated ones, the model is still
dominated by simulated data.

**Careful:** if you delete `data/experiences.csv` to create the simulated rows again, copy the
`experience report` rows first and add them back afterwards.

**How to replace them with real data:**
- **HSG experience reports** (public): extract only numbers (e.g. the stated monthly cost and housing
  type). Do not copy text and do not store names. Set `source` to `experience report`.
- Simply add the rows to the CSV (or delete the simulated rows) and run `python create_database.py`.

## 3. Live APIs

| API | Used for | URL | Key | Notes |
|-----|----------|-----|-----|-------|
| Frankfurter | exchange rates CHF → local currency | `https://api.frankfurter.dev/v1/latest` | none | reference rates of the European Central Bank; the last rates are saved in `data/last_rates.json` as a fallback |
| Open-Meteo archive | daily temperature and precipitation of the last 3 complete years | `https://archive-api.open-meteo.com/v1/archive` | none | free for non-commercial use; attribution: Open-Meteo.com |
| IMF DataMapper | yearly consumer price inflation of the USA (2023 to 2026) | `https://www.imf.org/external/datamapper/api/v1/PCPIPCH/USA` | none | the factor is used to bring the Kaggle prices (in US dollars) from 2022 to today |

**Live test on 2026-11-16** (from a cloud development environment):

| API | Result |
|-----|--------|
| Frankfurter | works – live rates of 2026-11-13 for all 10 currencies of our cities |
| Open-Meteo archive | works – 12 monthly averages returned for Copenhagen |

## 4. How the HSG portal was used

- Public pages only, no login. 15 search requests (one per university) and about 60 reports (page + PDF),
  with a pause of 4–5 seconds between requests, plus one search for the full list of partner universities.
- The result lists and reports contain the names of the authors. Nothing of that was saved in this
  repository: only the numbers in the tables above.

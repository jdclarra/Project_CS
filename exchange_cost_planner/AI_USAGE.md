# Use of generative AI – Exchange Cost Planner

The HSG rules on AI use, citation and the declaration of authorship apply to this project. This file
documents how GenAI was used. **The team must check every statement and adapt it to what really happened.**

## Tool

- **Claude** (Anthropic), used through Claude Code.

## What the AI did

| Area | Use |
|------|-----|
| Concept | Helped to compare project ideas, to refine the concept and to prepare questions for the coaching |
| Source code | **Generated the initial implementation of all Python files**: `app.py`, `database.py`, `create_database.py`, `calculation.py`, `currency.py`, `check_calculation.py`, `ml_model.py`, `external_data.py` |
| Data collection | **Claude in Chrome** opened all 1,304 HSG experience reports 2024/2025 and 2025/2026 and extracted the monthly costs of 123 reports into `data/experience_reports_raw.csv` (numbers only, no names, no text). Claude converted them to CHF for `data/experiences.csv`. The team should check a sample of rows against the reports |
| Data | Entered the first **placeholder** prices (now replaced by Kaggle prices and HSG experience reports); wrote the rules for the **simulated** training data |
| Documentation | Drafted README, DATA_SOURCES, SCHNITTSTELLEN, CONTRIBUTIONS, VIDEO_PLAN, TEST_CHECKLIST, REQUIREMENTS_AUDIT and this file |
| Testing | Ran automated tests of every page during development, including API failures |
| Clean-up | Removed the code and documentation of features the team had deleted (one-time costs, "Share your experience", excursion search) and simplified the code |
| Review | Compared the code with the course content and added the "Declaration of AI Assistance" comments; found that the country inflation was wrong for Kaggle prices in US dollars and changed it to the US inflation |

## Citation in the source code

We compared the code with the content of our course (Computational Basics, Python incl. classes,
Databases and SQL, Computer Networks, Data Science with NumPy, pandas, Matplotlib and Seaborn,
Machine Learning with regression, classification and KNN; see the ecoreps course summary). Everything that
goes beyond this content,
except standard Streamlit page elements from the Streamlit documentation, is marked in the code with a
comment that starts with:

```python
# Declaration of AI Assistance: ...
```

The comment says what was written or suggested by Claude. The most important parts are:

| File | Marked as AI-assisted |
|------|------------------------|
| `app.py` | all Plotly charts (the course uses Matplotlib and Seaborn), caching with `st.session_state`, reading information out of the `source` text with string methods, the inflation adjustment, the named aggregation and hover text of the world map, the chart with two y-axes, number formats in f-strings such as `{:,}` and `{:.0%}`, `datetime` |
| `database.py` | `sqlite3.connect` and query parameters (`?`), file paths with `os` |
| `create_database.py` | file handling with `os`, the NumPy random number generator, converting NumPy numbers for SQLite, building the `INSERT` statement, `if __name__ == "__main__"` |
| `calculation.py` | `datetime` calculations |
| `currency.py` | JSON file handling, `timeout` and `raise_for_status`, `try` / `except` |
| `external_data.py` | `datetime`, `.dt.month`, `try` / `except`, the IMF inflation factor |
| `ml_model.py` | random forest, mean absolute error, `LinearRegression` from scikit-learn, `pd.concat(axis=1)`, `reindex` |
| `check_calculation.py` | the whole check script |

Checked against the course summary on ecoreps: SQL `JOIN` (3.4.5), `raise ValueError` (2.4.1), `requests.get`
with `params` and `.json()` (4.5), `pd.merge`, `groupby` / `agg`, `pd.concat`, `pd.get_dummies`,
`pd.to_datetime`, `isinstance`, `train_test_split`, `lambda`, `break` and classes are part of the course
and are therefore not marked.

When you change or rewrite a part yourselves, add a line such as
`# Function compare_with_budget rewritten by <name>` so that it stays clear which parts are your own work.

## What the students did (fill in honestly)

- _e.g. had the project idea and defined the concept and the roles_
- _e.g. researched the real city prices and replaced the placeholders_
- _e.g. read the HSG experience reports and entered the prices of 23 cities_
- _e.g. reviewed and tested every page with TEST_CHECKLIST.md_
- _e.g. changed the lifestyle assumptions / charts / texts_
- _e.g. can explain every function of their own module_

## Reflection (fill in, also for the video)

- What worked well with AI? _…_
- Where was the AI wrong or unhelpful? _…_
- What did we have to check or fix ourselves? _…_
- What did we learn about programming by reviewing generated code? _…_

## Other aids

- Streamlit, pandas, scikit-learn and Plotly documentation
- API documentation of Frankfurter, Open-Meteo and the IMF DataMapper
- Lecture slides and exercises of the course
- _add further aids_

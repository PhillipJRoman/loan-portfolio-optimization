# Loan Portfolio Optimization

Given a pool of loan applicants and a fixed budget, select which loans to fund to maximize expected return under risk and policy constraints. Capstone project for DSCI 591 at Drexel University.

## Team

- Ashay Patla
- Ryan Quinlan
- Phillip Roman

## Dataset and Target Definition

Fannie Mae Single-Family Loan Performance Data, 2017 vintage, [publicly available](https://capitalmarkets.fanniemae.com/credit-risk-transfer/single-family-credit-risk-transfer/fannie-mae-single-family-loan-performance-data). Four quarterly acquisition files with monthly performance records, aggregated to one row per loan. 2,046,511 loans after cleaning.

A loan is labeled as defaulted (1) if it reached 180 days delinquent or ended in a credit event disposition:

```
default_flag = (max_dlq_ever >= 6) OR (zero_bal_code in {02, 03, 09, 15})
```

The 180-day threshold follows Basel II/III, which permits it for residential mortgages because home loans cure at substantially higher rates than other retail exposures. 15.09% of the book went delinquent at some point; 3.41% reached 180 days.

## Approach

Four stages. EDA is owned by one track, the modeling pipeline by another.

**Machine learning.** Four models trained on 18 features to predict `default_flag`, producing a calibrated probability of default (PD) per loan rather than a binary classification. A rule-based lookup table scoring loans by credit grade crossed with LTV band serves as the non-ML baseline. Split 60/20/20 by hashing `LOAN_ID`.

**Linear programming.** Gurobi, fractional formulation over the 409,857-loan test pool. Objective is expected return, `(1 - PD) x interest_income_7yr - PD x loss_if_default`. Constraints: budget at 10% of pool UPB, average PD ceiling, 6% per-state cap, and minimum shares for first-time buyer, HomeReady, and HFA loans.

**Monte Carlo simulation.** Vasicek model over 10,000 seven-year paths, with a national factor, a per-state factor, and an idiosyncratic factor per loan. Total asset correlation of 0.15 per Basel, split 79/21 between national and state. Sensitivity grid over asset correlation (0.00, 0.15, 0.30) crossed with LGD (30%, 50%).

Six portfolios were compared: two scoring methods crossed with three selection rules (risk-sort, greedy-return, LP).

## Results

| Model | Test AUC | Train AUC | Gap | ECE |
|---|---|---|---|---|
| CatBoost (tuned) | 0.7725 | 0.7781 | 0.0056 | 0.00054 |
| XGBoost | 0.7747 | 0.8068 | 0.0320 | 0.00101 |
| LightGBM | 0.7737 | 0.8254 | 0.0517 | 0.00093 |
| Logistic regression | 0.7666 | 0.7686 | 0.0020 | 0.00077 |
| Rule-based lookup | 0.7131 | — | — | — |

Tuned CatBoost was selected on the train-test gap rather than AUC, which separates the four models by less than 0.008. All four are calibrated near the measurement floor; isotonic regression was tested and rejected.

Portfolio returns in $M, scored on observed defaults against a $9.376B budget:

| | risk-sort | greedy-return | LP |
|---|---|---|---|
| Rule-based | 2,272.0 | 2,723.8 | 2,707.0 |
| CatBoost | 2,190.4 | 2,806.9 | 2,778.8 |

A better score only pays when the selection rule uses it to pursue return. CatBoost beats the rule-based lookup by $83M under greedy-return and loses by $81M under risk-sort, since the loans least likely to default also carry the lowest rates. The model's advantage concentrates in adverse outcomes, growing from 0.7 points on average to 3.8 points in the worst 5% of simulated years. The state concentration cap functions as designed, with the gap between capped and uncapped portfolios tracking the California factor at +0.78 correlation, but the downside protection it buys is offset by the upside it forgoes.

## Setup

```console
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

Gurobi requires a license; an academic license was used here. Raw quarterly files are gitignored and available at the Fannie Mae link above; `src/reduce_fannie.py` aggregates them to loan level.

## Directory Layout

- `data/raw/` — quarterly acquisition and performance files
- `data/processed/` — loan-level, typed, and scored parquet files, plus simulation outputs
- `data/models/` — saved model artifacts and per-model results JSON
- `eda/` — EDA notebooks 01–05 and markdown summaries
- `ml-lp-sim/` — production notebooks (`05_production_ml`, `_lp`, `_sim`), earlier scaffolds, and summaries
- `src/` — data reduction and summary generation scripts
- `feature_classification.md` — feature inventory and leakage classification

Notebooks run from their own directory using relative paths.

## Stack

Polars, scikit-learn, XGBoost, LightGBM, CatBoost, Gurobi (gurobipy), NumPy, Matplotlib.

## References

- **Primary reference.** Sirignano, J., Tsoukalas, G., Giesecke, K. "Large-Scale Loan Portfolio Selection." SSRN 2641301, 2016.
- **Vasicek model.** Vasicek, O. "Probability of Loss on Loan Portfolio." KMV Corporation, 1987.
- **Basel framework.** Basel Committee on Banking Supervision. Basel II/III. Source of the 180-day default definition and the 0.15 asset correlation for residential mortgage exposures.
- **Concentration limits.** Office of the Comptroller of the Currency. Comptroller's Handbook: Concentrations of Credit, 2020.
- **Affordable housing goals.** Federal Housing Finance Agency. 12 CFR Part 1282.
- **Data glossary.** Fannie Mae. Single-Family Loan Performance Data Glossary.

## License

Developed for educational purposes as part of DSCI 591 coursework at Drexel University.
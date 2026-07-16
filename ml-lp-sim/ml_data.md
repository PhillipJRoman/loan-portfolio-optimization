# ML Stage: Data Decisions

Decisions log for the ML track. What we chose, why, and what is still open.

Companion: `feature_notes.md` covers which columns are admissible and the
findings worth sharing with the EDA track.

**Status key:** `LOCKED` decided | `OPEN` needs a decision | `PARKED` deliberately
deferred

---

## Two reversals

Both were marked LOCKED in the first revision and both changed once we had data.
Recording them rather than editing quietly.

**Isotonic calibration: dropped.** Original reasoning was sound but rested on an
assumption that turned out false. We assumed the models would need calibrating.
They did not. Detail in the calibration section.

**Stratified split: not stratified.** Exact stratification cost a shuffle, a
window function, and a 2M-row string join, and bought a default-rate drift of
~0.03%. Switched to a hash. Detail in the split section.

---

## File lineage

| File | Status |
|---|---|
| `fannie_2017_features_added.parquet` | Frozen. EDA track owns it. Never modify. |
| `fannie_2017_typed.parquet` | Ours. All 123 columns, types cast. Serves both tracks. |

`LOCKED` Never overwrite a file another track reads.

`LOCKED` Typed file keeps all 123 columns, not just model features. EDA needs
working `OLTV` / `DTI` too, so one file serves both. Feature selection lives in
code as a keep-list, not baked into a file. At 46MB, trimming columns saves
nothing.

`LOCKED` No third file. The split and feature prep are cheap and deterministic,
so `df` and `feat` stay in memory. A `fannie_2017_model.parquet` was drafted and
abandoned: writing 2M rows on every iteration cost minutes and bought nothing.

---

## Target

`LOCKED` `default_flag` = D180 delinquency, or short sale, or foreclosure.
Verified: 69,886 positives, 3.4143%.

Label window is cumulative over the full ~8-year observation period.

`LOCKED` No fixed-horizon relabeling. A 24-month window would only observe
through 2019, a benign pre-COVID stretch, discarding the defaults that make this
vintage interesting. It would also break the naive baseline threshold, which is
the 8-year COVID-inclusive 3.4% rate.

---

## Type casts

`LOCKED` Seven columns cast to numeric. Verified: zero unparseable values, cast
is lossless, null counts unchanged.

| Column | To | Column | To |
|---|---|---|---|
| `OLTV` | Float64 | `CSCORE_C` | Int32 |
| `OCLTV` | Float64 | `NUM_BO` | Int32 |
| `DTI` | Float64 | `NO_UNITS` | Int32 |
| `MI_PCT` | Float64 | | |

`LOCKED` The cast step does types only. No fills, no drops, no derived columns.
Isolates failure, and the EDA track may want nulls as nulls.

Verified ranges, no sentinels: `OLTV` max 97 with zero above 100, `DTI` max 63,
`CSCORE_C` min 620, `MI_PCT` min 6, `ORIG_UPB` 969 distinct.

---

## Null rules

All implemented in feature prep. Verified: zero nulls after.

| Column | Nulls | Rule | Why |
|---|---|---|---|
| `MI_PCT` | 1,432,111 | → 0 | Structural. Zero coverage is the true value. |
| `MI_TYPE` | 1,432,111 | → `"NONE"` | Same loans, confirms the reading. |
| `CSCORE_C` | 1,083,143 | → 0 + `has_coborrower` | Structural. No co-borrower score to estimate. The 0 is inert padding; the indicator carries the meaning. |
| `CSCORE_B` | 1,573 | → median + `fico_missing` | Missing FICO may itself be signal. |
| `DTI` | 340 | → median | 0.017%. Too small for an indicator to be estimable. |

`LOCKED` No mean-imputation on `CSCORE_C` or `MI_PCT`. Filling `MI_PCT` at ~27%
would assert that 1.4M uninsured loans carry insurance.

---

## Features

`LOCKED` Admissibility rule: knowable on the day the loan closed. Roughly 60 of
123 columns fail it. Full classification in `feature_notes.md`.

**Final set: 26 features.** 11 numeric + 5 flags + 10 categorical.

- Numeric: `CSCORE_B`, `CSCORE_C`, `OLTV`, `OCLTV`, `DTI`, `ORIG_RATE`,
  `ORIG_UPB`, `ORIG_TERM`, `NUM_BO`, `NO_UNITS`, `MI_PCT`
- Flags: `is_first_time`, `is_homeready`, `is_hfa`, `has_coborrower`,
  `fico_missing`
- Categorical: `CHANNEL`, `SELLER`, `PURPOSE`, `PROP`, `OCC_STAT`, `STATE`,
  `MI_TYPE`, `HIGH_BALANCE_LOAN_INDICATOR`,
  `PROPERTY_INSPECTION_WAIVER_INDICATOR`, `RELOCATION_MORTGAGE_INDICATOR`

**Dropped:**

| Column | Why |
|---|---|
| `PRODUCT`, `PPMT_FLG`, `IO` | Constants. Verified `n_unique = 1`. |
| ARM block | All-FRM book confirms it is dead. |
| `FIRST_FLAG` | Verified exact duplicate of `is_first_time`. Cross-tab shows N→0, Y→1, no off-diagonal. |
| `credit_grade` | Reserved for the naive scorer. Collinear with `CSCORE_B`. |
| `orig_quarter` | Admissible, but feeding origination timing to the model invites it to learn the seasoning artifact we treat as a limitation. |

`LOCKED` `SELLER` stays. It carries signal beyond FICO/LTV/DTI: rates span
2.21%-8.48% and loan mix does not explain it. Cardinality is 38, not hundreds,
because Fannie pre-buckets small originators into `Other`.

`LOCKED` Quicken merged. `Quicken Loans, Llc` and `Quicken Loans Inc.` are the
same book (3.04% vs 3.06%, FICO 740 vs 741). 38 → 37.

`LOCKED` `CSCORE_B` is the model feature; `credit_grade` is for EDA and the naive
scorer. Never both.

---

## Split

`LOCKED` Hash-based: `hash(LOAN_ID, seed=591) % 100`. 0-59 train, 60-79 calib,
80-99 test.

Deterministic, so any teammate reruns and gets identical splits with no stored
seed. Pure column math: no shuffle, no window, no join.

| Split | n | Positives | Rate |
|---|---|---|---|
| train | 1,227,572 | 41,810 | 0.034059 |
| calib | 409,353 | 14,094 | 0.034430 |
| test | 409,926 | 13,982 | 0.034109 |

**Reversal from stratified.** Drift is ~0.03%, verified: all three splits landed
within one standard deviation of expected positives. Invisible to AUC and
calibration. Verified empirically instead of guaranteed structurally.

`LOCKED` No temporal split. Within one vintage every loan lived through the same
calendar, so an origination-date split only tests whether autumn originations
differ from spring ones. A real out-of-time test needs a second vintage.

`LOCKED` PDs feeding the LP come from `test`, which the model never trained on.

**Documented limitation.** Seasoning: a December 2017 loan has ~0.9 fewer years of
exposure than a January one. Default hazard peaks around years 2-4 and is flat by
year 7, so with 8 years of data the gap falls where little is happening.

---

## Models

`LOCKED` Evaluated on AUC and calibration, not accuracy. At a 3.4% base rate,
predicting "never defaults" scores 96.6% accuracy and is useless.

| Model | Test AUC | Train | Gap | Brier | ECE | Fit |
|---|---|---|---|---|---|---|
| Logistic regression | 0.7705 | 0.7731 | 0.0026 | 0.031580 | 0.00103 | 6s |
| XGBoost | 0.7781 | 0.8165 | 0.0384 | 0.031481 | 0.00123 | 6s |
| LightGBM | 0.7768 | 0.8377 | 0.0609 | 0.031502 | 0.00114 | 11s |
| CatBoost | 0.7750 | 0.7814 | 0.0064 | 0.031480 | 0.00086 | 75s |

Baseline: synthetic PD generator scored 0.7178 on three hand-set coefficients.

**The signal is mostly linear.** Trees beat logistic regression by 0.006-0.008.
Real at 410k rows, small in practice. CatBoost was run as a check, not a
candidate: it is built for high-cardinality categoricals and overfitting
resistance, and its ordered boosting cut the gap from 0.038 to 0.0064 while
gaining no AUC. So overfitting was never the constraint. The ceiling is the data.

`LOCKED` **CatBoost selected.** AUC and Brier are ties (0.0031 is inside noise at
13,982 positives; Brier separates at the sixth decimal). The train-test gap does
not tie: 6x smaller. That matters because our calibration result carries an IID
caveat, and shipping the model with the larger gap alongside that caveat is a
weak position.

`LOCKED` No class weighting or resampling. Both distort predicted probabilities,
and calibrated probabilities are the product of this stage. This was `OPEN`; the
calibration result closed it.

`PARKED` Tuning. `depth=6` / 400 iterations were a guess. The ceiling argument
says tuning buys 0.001-0.003. Track 1 delivers the tuned model in week 6 per the
launch report.

---

## Calibration

`LOCKED` **Ship raw predictions. No isotonic.** Reverses the original decision.

All four models were already calibrated at ECE 0.0009-0.0012 against a base rate
of 3.4%, meaning the average bin is off by a tenth of a percentage point.

Expected in hindsight: all four minimize log-loss, a proper scoring rule that is
lowest exactly when predicted probability equals true probability. Calibration is
what training was already asking for. Add 1.2M rows and no class weighting and
there is little left to fix.

**ECE has a floor.** At ~41k loans per bin, sampling noise is ~±0.0008, so a
perfect model would still score ~0.0006 here. CatBoost at 0.00086 is 1.4x the
floor: about as good as this test set can measure.

**Isotonic was tested and did nothing.**

| model | ECE raw | ECE iso | delta | AUC raw | AUC iso |
|---|---|---|---|---|---|
| logreg | 0.00103 | 0.00117 | +0.00014 | 0.7705 | 0.7702 |
| xgboost | 0.00123 | 0.00100 | -0.00023 | 0.7781 | 0.7780 |
| lightgbm | 0.00114 | 0.00096 | -0.00018 | 0.7768 | 0.7766 |
| catboost | 0.00086 | 0.00094 | +0.00008 | 0.7750 | 0.7747 |

Every delta is below the measurement floor. Two improved, two worsened: that is
noise. It cost AUC on all four, because isotonic maps distinct predictions to the
same value and destroys ranking. And it introduced PD = 0 on 3,168 CatBoost loans,
which would tell the LP those loans cannot default.

**Platt considered, declined.** It would not have produced either problem: a
sigmoid never reaches 0, and it is strictly increasing so it preserves ranking.
But with nothing to correct, the best case is doing nothing gracefully instead of
doing nothing clumsily. One null result is enough.

**Why isotonic looked right going in:** 70k positives, so it cannot overfit at
that scale. True for the middle of the distribution. It broke in the tails, where
the blocks thin to single digits regardless of total sample size. The max PDs
came back as 0.75 and 4/9 and 2/7, which are fractions of a handful of loans.

**IID caveat, for the report.** Train and test were assigned at random, so both
come from the same 2017 pool and look alike (independent and identically
distributed). That is the easiest case for calibration to carry over, and not
what a deployed model faces. A lender trains on old vintages and scores
applicants in a different economy. State this rather than claiming the models are
calibrated in general.

---

## Naive baseline scorer

`LOCKED` Rule-based lookup: default rate by `credit_grade` x LTV band, built on
`train` only.

Exists because our claim is that calibrated probabilities plus optimization beat
a naive rule. If the naive rule ranked by CatBoost's PDs, both strategies would
share the same risk numbers and we would only be testing LP vs greedy.

- FICO half: `credit_grade`, already built. 5 levels.
- LTV half: cuts at 60/70/80/90/95. Mirrors underwriting; 80 is the MI boundary.
- 5 x 6 = 30 buckets.
- Buckets under 500 loans fall back to the FICO grade's overall rate. Still
  rule-based, just coarser.

`LOCKED` Built on train only. Using test would leak answers into the baseline and
flatter it.

---

## Economics

Not ML decisions, but they consume the ML output.

| Column | Value |
|---|---|
| `lgd` | Flat 0.30. Verified: 1 distinct value, no nulls, identical across both classes. Sirignano good-economy number. |
| `loss_if_default` | `lgd` x `ORIG_UPB` |
| `interest_income_7yr` | 7-year interest, horizon-matched to the label |

**Objective:** `c_i = (1 - PD_i) x interest_income_7yr_i - PD_i x loss_if_default_i`

**Why 7 years.** PD is an ~8-year cumulative probability. Pairing it with 30-year
interest would bias the objective toward risk: upside accrues 30 years, downside
has 8 to appear. Also proxies prepayment (30-year median life ~7 years) and is
not a token slice, since ~36% of lifetime interest is earned in the first 7 years.

**Limitations:**

1. `loss_if_default` uses `ORIG_UPB`, but a loan defaulting in year 4 has
   amortized to ~90% of original. Loss overstated ~10%. Conservative and roughly
   proportional, so minimal effect on LP ranking.
2. Defaulted loans are credited zero interest, when payments were collected until
   default. Also conservative.
3. **Capital velocity unmodeled.** A 15-year returns ~$81k principal by year 7 vs
   ~$28k for a 30-year on the same $200k. Worth nothing in a single-period model.
   23% of the book is not a 30-year loan, so this is not a corner case.

---

## Open and parked

| Item | Status | Note |
|---|---|---|
| Tuning | `PARKED` | Track 1 owns it, week 6. |
| Applicant pool construction | `PARKED` | Sampled pools (n=20k, repeated) give error bars on the headline claim vs one shot at the full test split. Does not block. |
| Attribution 2x2 | `PARKED` | Whether the report separates "gain from better PDs" vs "gain from optimization." Scorer and selector are swappable regardless. |
| `MSA` / `ZIP` | `PARKED` | Admissible, high cardinality. Out of first pass. |
| Representative FICO | `PARKED` | Fannie's convention is the lower of borrower scores. `min(CSCORE_B, CSCORE_C)` coalesced to `CSCORE_B` is what an underwriter uses. |
| Second-lien feature | `PARKED` | `OCLTV - OLTV`. `OCLTV` maxes at 114 vs `OLTV` at 97, so real subordinate financing exists. |

**Parked for stage 3: expected return may be positive everywhere.** Setting
`c_i = 0` gives break-even `PD = I / (L + I)`. For a 30-year at 4.29%,
`I/UPB ≈ 0.26`, so break-even is ~47%. For a 15-year at 3.48%, ~40%. The top
decile averages 12% PD. If no loan clears 40%, every loan has positive expected
return, the budget constraint does all the work, and the average-PD ceiling is
the only real risk control. Check max PD in stage 3.

---

## Change log

| Date | Change |
|---|---|
| 2026-07-16 | Initial. Lineage, target, casts, null semantics, split, calibration, economics. |
| 2026-07-16 | Rev 2. Casts and split verified. Null rules implemented and locked. Feature set final at 26. Four models fit; CatBoost selected. Isotonic tested and dropped, reversing the original decision. Stratified split reversed to hash. Class imbalance closed as no-weighting. Naive scorer design locked. |

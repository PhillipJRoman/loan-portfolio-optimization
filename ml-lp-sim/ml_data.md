# ML Stage: Data Decisions

Decisions log for the ML track (Phillip). Every data-level choice, why it was
made, and what is still open.

Companion doc: `feature_classification.md` covers which columns are admissible
and why. This doc does not repeat those tables.

**Status key**
- `LOCKED` — decided, do not revisit without team discussion
- `PROPOSED` — recommended, not yet ratified
- `OPEN` — needs a decision
- `PARKED` — deliberately deferred, revisit later

---

## File lineage

| File | Owner | Status |
|---|---|---|
| `fannie_2017_features_added.parquet` | EDA track | **Frozen.** Never modify. |
| `fannie_2017_typed.parquet` | ML track | Types corrected. Serves both tracks. |

- `LOCKED` Never overwrite a file another track is reading. Each transformation writes a new parquet.
- `LOCKED` Cast file keeps **all 123 columns**, not just model features.
  - EDA track needs working `OLTV` / `DTI` too. One file serves both.
  - Feature selection lives in code as a keep-list constant, not baked into a file. Changing our mind means editing a list, not regenerating a parquet.
  - 46MB. Trimming columns saves nothing.

---

## Target

- `LOCKED` `default_flag` = D180 delinquency **or** short sale **or** foreclosure.
- Observed rate: **3.4143%** (verified on 2,046,851 rows).
- Label window: cumulative over the full observation window, roughly 8 years (2017 origination, data through ~2025).
- `LOCKED` No fixed-horizon relabeling (e.g. "default within 24 months").
  - A 24-month window only observes through 2019, a benign pre-COVID stretch. It would discard the defaults that make this vintage interesting.
  - The naive baseline threshold is the 3.4% historical rate, which is an 8-year COVID-inclusive number. Changing the label would break that alignment.

---

## Type casts

- `LOCKED` Seven columns arrived as `String` and were cast to numeric.

| Column | Cast to | Reason it was text |
|---|---|---|
| `OLTV` | Float64 | Raw Fannie files are pipe-delimited with no type header |
| `OCLTV` | Float64 | same |
| `DTI` | Float64 | same |
| `MI_PCT` | Float64 | same |
| `CSCORE_C` | Int32 | same |
| `NUM_BO` | Int32 | same |
| `NO_UNITS` | Int32 | same |

- Verified before casting: **zero unparseable values** across all seven. No junk strings, no `"N/A"`, no empties. Cast is lossless.
- `LOCKED` The cast step does types **only**. No fills, no drops, no derived columns.
  - Isolates failure. If something breaks downstream we know it was not the cast.
  - EDA track may want to see nulls as nulls.
- Only four raw columns arrived numeric: `ORIG_RATE`, `ORIG_UPB`, `ORIG_TERM`, `CSCORE_B`.

---

## Null semantics

The headline null counts are misleading. Two of the three large ones are not
missing data at all.

| Column | Nulls | % | Meaning |
|---|---|---|---|
| `CSCORE_C` | 1,083,143 | 52.9% | **Structural.** No co-borrower exists. Aligns exactly with `NUM_BO = 1`. |
| `MI_PCT` | 1,432,111 | 70.0% | **Structural.** No mortgage insurance exists. MI is required above 80 LTV; nulls are the sub-80 loans. |
| `DTI` | 340 | 0.017% | **Genuinely missing.** |
| `OLTV`, `OCLTV`, `NUM_BO`, `NO_UNITS` | 0 | 0% | Clean. |

- `LOCKED` Do **not** mean-impute `CSCORE_C` or `MI_PCT`. Filling `MI_PCT` with a mean of ~27% would assert that 1.4M uninsured loans carry insurance.
- `PROPOSED` `MI_PCT` null fills to **0**. Zero coverage is the true value, not a guess.
- `PROPOSED` `CSCORE_C` gets a missing indicator, not a numeric fill. There is no "co-borrower score" to estimate when there is no co-borrower.
- `OPEN` `DTI`'s 340 nulls: drop the rows or impute. 0.017% either way, so this is a footnote, but it needs a stated rule.
- `OPEN` `CSCORE_B` nulls: 1,573 rows (0.08%), visible as `credit_grade = "Unknown"`. Recommend a missing indicator over dropping, since missing FICO may itself be signal.

**Note for EDA track:** "70% missing, unusable" is the wrong read on `MI_PCT`. The nulls are informative.

---

## Feature admissibility

- `LOCKED` A feature is admissible only if a lender could have known it on the day the loan closed.
- `LOCKED` Roughly 60 of 123 columns are performance-era or disposition-era and are excluded. Full classification in `feature_classification.md`.
- Highest-severity leaks: `max_dlq_ever` and `zero_bal_code` construct the label directly. Either one returns AUC near 1.00.
- Named trap: `ORIGINAL_LIST_PRICE` is the **REO listing price** of the foreclosed property, not the purchase price. Origination-sounding name, perfect leakage.

### Collinear pairs (never include both)

- `CSCORE_B` / `credit_grade`
- `CSCORE_B` / `ORIG_CLASSIC_FICO`
- `FIRST_FLAG` / `is_first_time`
- `HOMEREADY_PROGRAM_INDICATOR` / `is_homeready`

### Division of labor between FICO representations

- `LOCKED` `CSCORE_B` (continuous) is the model feature.
- `LOCKED` `credit_grade` (FICO bins: Exceptional / Very Good / Good / Fair-Poor / Unknown) is for EDA and the naive baseline scorer. Not a model feature.

---

## Split strategy

- `LOCKED` **Stratified random** on `default_flag`, three-way: train / calibration / test.
- `LOCKED` **No temporal split.**
  - Within a single vintage, every loan lived through the same calendar: same 2018, same 2020, same forbearance programs. An origination-date split does not test macro generalization, only whether autumn originations differ from spring ones.
  - A real out-of-time test requires a second vintage (train 2017, score 2018), not a slice of 2017.

| Split | Purpose |
|---|---|
| Train | Fit LogReg / XGBoost / LightGBM. Also build the FICO x LTV baseline scorer here, and only here. |
| Calibration | Fit isotonic. Untouched by training. |
| Test | Evaluate AUC + calibration curves. This is the applicant pool feeding the LP. |

- `LOCKED` PDs feeding the LP must come from loans the model never trained on.
- At 60/20/20 and 3.4%, each held-out split carries roughly 13,600 positives. Ample for isotonic.

### Documented limitation

Seasoning bias: a December 2017 loan has ~0.9 fewer years of exposure than a
January 2017 loan. Mortgage default hazard peaks around years 2 to 4 and is
nearly flat by year 7, so with 8 years of observation the differential falls in a
region where little is still happening. Named as a limitation, not designed
around.

---

## Model and calibration

- `LOCKED` Three models: Logistic Regression (interpretable baseline), XGBoost, LightGBM.
- `LOCKED` Evaluated on **AUC and calibration curves**, not accuracy. At 3.4% base rate, predicting "never defaults" scores 96.6% accuracy and is useless.
- `LOCKED` Calibration via **isotonic regression** on a dedicated calibration split.
  - Enough positives at this scale that isotonic will not overfit.
  - No reason to force a sigmoid shape.
- `OPEN` Class imbalance handling: class weights, undersampling, or nothing. Decide after seeing baseline AUC and calibration.
  - Note: resampling distorts predicted probabilities, and calibrated probabilities are the entire product of this stage. Class weights are the safer default if anything is needed at all.

---

## Economics constants

Not ML decisions, but they consume the ML output, so recorded here.

| Column | Value | Source |
|---|---|---|
| `lgd` | Flat **0.30**, all rows | Sirignano et al. good-economy round number |
| `loss_if_default` | `lgd` x `ORIG_UPB` | derived |
| `interest_income_7yr` | 7-year interest | horizon-matched to the label |

- Verified: `lgd` has 1 distinct value, 0.30, zero nulls, identical across both classes. Confirmed flat, not back-computed from realized foreclosure outcomes.
- `interest_income_7yr` is horizon-matched: PD is an ~8-year cumulative probability, so pairing it with 30-year lifetime interest would bias the objective toward risk (upside accrues 30 years, downside has 8 to appear). Also serves as a rough prepayment proxy (30-year mortgages have a median life near 7 years).

### Objective

```
c_i = (1 - PD_i) x interest_income_7yr_i  -  PD_i x loss_if_default_i
```

### Stated limitations

- `loss_if_default` uses `ORIG_UPB`, but a loan defaulting in year 4 has amortized to ~90% of original balance. Loss overstated ~10%. Conservative and roughly proportional across loans, so minimal effect on LP ranking.
- The objective credits defaulted loans with zero interest income, when payments were collected until default. Also conservative.

---

## Open decisions

| Item | Status | Notes |
|---|---|---|
| `DTI` null rule | `OPEN` | 340 rows. Drop or impute. |
| `CSCORE_B` null rule | `OPEN` | 1,573 rows. Indicator recommended. |
| Class imbalance | `OPEN` | Decide after baselines. |
| `MSA` / `ZIP` | `PARKED` | Legitimate but high cardinality. Out of first pass. |
| ARM columns | `PARKED` | Admissible but likely near-zero variance for a 2017 fixed-rate book. Check variance, expect to drop the block. |
| `ISSUE_SCOREB` / `ISSUE_SCOREC` / `ISSUE_CLASSIC_FICO` | `PROPOSED` exclude | Measured at securitization, not origination. Near-identical to `CSCORE_B`, so excluding costs nothing and keeps the origination-only rule clean. |
| Representative FICO | `PARKED` | Fannie convention is the **lower** of borrower scores. `min(CSCORE_B, CSCORE_C)` coalesced to `CSCORE_B` is likely stronger than either alone. Feature engineering, revisit after baselines. |
| Applicant pool construction | `PARKED` | Sampled pools (n=20k, repeated) give error bars on the headline claim vs one shot at the full test split. Does not block ML. |
| Attribution 2x2 | `PARKED` | Whether the report needs to separate "gain from better PDs" vs "gain from optimization." Costs nothing to keep open; scorer and selector are being written as swappable pieces regardless. |

---

## Change log

| Date | Change |
|---|---|
| 2026-07-16 | Initial. Lineage, target, casts, null semantics, split, calibration, economics. |

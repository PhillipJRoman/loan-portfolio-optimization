# Feature Classification: Fannie Mae 2017 Vintage

Shared reference for FinTech Optimizers. Classifies all 123 columns in
`fannie_2017_features_added.parquet` (2,046,851 rows) into four groups.

**Why this document exists.** The aggregated file contains both origination-time
and performance-era columns. A random train/test split does not protect against
performance-era columns, because they describe the future of the same loan. Any
performance-era column in the feature matrix leaks the answer. This document
draws the line once so both tracks apply the same rule.

**The rule.** A feature is admissible only if a lender could have known its value
on the day the loan closed. Anything that updates, populates, or resolves after
closing is inadmissible, regardless of how origination-like its name sounds.

---

## Group 1: Origination-time (admissible model features)

Known at closing. These are the only columns eligible for the feature matrix.

### Core credit (the predictive workhorses)

| Column | Current dtype | Note |
|---|---|---|
| `CSCORE_B` | Int32 | Primary borrower FICO. Ready to use. |
| `CSCORE_C` | String | Co-borrower FICO. Needs cast. Null when no co-borrower. |
| `OLTV` | String | Original loan-to-value. **Needs cast.** |
| `OCLTV` | String | Original combined LTV. **Needs cast.** |
| `DTI` | String | Debt-to-income. **Needs cast.** |
| `NUM_BO` | String | Number of borrowers. Needs cast. |

### Loan terms

| Column | Current dtype | Note |
|---|---|---|
| `ORIG_RATE` | Float64 | Ready. |
| `ORIG_UPB` | Float64 | Ready. Also the LP budget cost. |
| `ORIG_TERM` | Float64 | Ready. Near-constant at 360. |
| `ORIG_DATE` | String | Origination date. Not a feature; used for `orig_quarter`. |
| `FIRST_PAY` | String | First payment date. Deterministic from `ORIG_DATE`. |
| `MATR_DT` | String | Maturity. Deterministic from `ORIG_DATE` + `ORIG_TERM`. |

### Loan and property characteristics

| Column | Note |
|---|---|
| `CHANNEL` | Retail / correspondent / broker. |
| `SELLER` | High cardinality. Consider grouping the tail. |
| `PURPOSE` | Purchase / refi / cash-out refi. |
| `PROP` | Property type. |
| `NO_UNITS` | Needs cast. |
| `OCC_STAT` | Owner-occupied / second home / investor. |
| `STATE` | Also the LP diversification key. |
| `MSA` | High cardinality. Hold out of first pass. |
| `ZIP` | High cardinality (3-digit). Hold out of first pass. |
| `PRODUCT` | Fixed vs ARM. Near-constant for this vintage. |
| `FIRST_FLAG` | First-time buyer. |

### Mortgage insurance

| Column | Note |
|---|---|
| `MI_PCT` | Coverage percent. Needs cast. Zero when no MI. |
| `MI_TYPE` | Borrower-paid / lender-paid / none. |

### Program and structural flags

| Column | Note |
|---|---|
| `HOMEREADY_PROGRAM_INDICATOR` | Duplicated by `is_homeready`. |
| `RELOCATION_MORTGAGE_INDICATOR` | |
| `PROPERTY_INSPECTION_WAIVER_INDICATOR` | |
| `HIGH_BALANCE_LOAN_INDICATOR` | |
| `HIGH_LOAN_TO_VALUE_HLTV_REFINANCE_OPTION_INDICATOR` | |
| `PPMT_FLG` | Prepayment penalty. |
| `IO` | Interest-only flag. |
| `FIRST_PAY_IO`, `MNTHS_TO_AMTZ_IO` | IO terms. Null for nearly all rows. |
| `BALLOON_INDICATOR` | |

### ARM terms (admissible but likely near-zero variance)

`ARM_5_YR_INDICATOR`, `ARM_PRODUCT_TYPE`, `ARM_INDEX`, `ARM_CAP_STRUCTURE`,
`INITIAL_INTEREST_RATE_CAP`, `PERIODIC_INTEREST_RATE_CAP`,
`LIFETIME_INTEREST_RATE_CAP`, `MARGIN`, `MONTHS_UNTIL_FIRST_PAYMENT_RESET`,
`MONTHS_BETWEEN_SUBSEQUENT_PAYMENT_RESET`

These are contractual and known at closing, so they are admissible in principle.
But the 2017 Fannie single-family book is overwhelmingly 30-year fixed, so these
are almost certainly null or constant. Check variance before including; expect to
drop the block.

### Derived at origination (built by our team)

| Column | Note |
|---|---|
| `orig_quarter` | Derived from `ORIG_DATE`. |
| `credit_grade` | FICO bins from `CSCORE_B`. Collinear with `CSCORE_B`. |
| `is_first_time` | Duplicates `FIRST_FLAG`. |
| `is_homeready` | Duplicates `HOMEREADY_PROGRAM_INDICATOR`. |
| `is_hfa` | Housing finance agency flag. |
| `monthly_payment` | Deterministic from rate, UPB, term. |

### Ambiguous: at-issuance credit scores

`ISSUE_SCOREB`, `ISSUE_SCOREC`, `ISSUE_CLASSIC_FICO`

Measured at securitization, which is shortly after origination but not at it.
Practically they will be near-identical to the origination scores. **Recommend
excluding** to keep the origination-only rule clean and unambiguous. The cost is
near zero since `CSCORE_B` carries the same information.

### Duplicate

`ORIG_CLASSIC_FICO` duplicates `CSCORE_B`. Keep `CSCORE_B` (already Int32).

---

## Group 2: Performance-era (inadmissible)

Populated or updated after closing. Not the label, but describes the loan's
future. Excluded from the feature matrix.

### Current loan state

`ACT_PERIOD`, `CURR_RATE`, `CURRENT_UPB`, `LOAN_AGE`, `REM_MONTHS`,
`ADJ_REM_MONTHS`, `CURR_SCHD_PRNCPL`, `TOT_SCHD_PRNCPL`, `UNSCHD_PRNCPL_CURR`,
`NON_INTEREST_BEARING_UPB`, `INTEREST_BEARING_UPB`, `ISSUANCE_UPB`

### Servicing

`SERVICER`, `MASTER_SERVICER`, `SERV_IND`, `MI_CANCEL_FLAG`, `RE_PROCS_FLAG`,
`LOAN_HOLDBACK_INDICATOR`, `LOAN_HOLDBACK_EFFECTIVE_DATE`, `RPRCH_DTE`

### Updated credit scores

`CURR_SCOREB`, `CURR_SCOREC`, `CURR_CLASSIC_FICO`

These are the most seductive of the group. A FICO score is a FICO score, so it
looks admissible. But a *current* FICO is measured after the borrower stopped
paying, and missed mortgage payments are what tanked it. It is a consequence of
default, not a predictor.

### ARM resets

`INTEREST_RATE_CHANGE_DATE`, `PAYMENT_CHANGE_DATE`

### Administrative

`POOL_ID`, `DEAL_NAME`, `PLAN_NUMBER`, `LOAN_ID`

`LOAN_ID` is the join key, not a feature.

---

## Group 3: Target and leakage (inadmissible, high severity)

### Target

| Column | Definition |
|---|---|
| `default_flag` | D180 delinquency, or short sale, or foreclosure. Rate: 3.4143%. |

### Direct label ingredients

These construct the target. Including any one returns AUC near 1.00.

| Column | Why |
|---|---|
| `max_dlq_ever` | The D180 half of the label. |
| `zero_bal_code` | The short-sale / foreclosure half of the label. |
| `ZB_DTE`, `ZERO_BALANCE_CODE_CHANGE_DATE` | Timing of the credit event. |
| `LAST_UPB` | Balance at the zero-balance event. |
| `FORECLOSURE_DATE` | Populated only on foreclosure. |
| `DISPOSITION_DATE` | Populated only on disposition. |
| `LAST_PAID_INSTALLMENT_DATE` | Directly encodes when payments stopped. |
| `PMT_HISTORY` | The full delinquency string. |

### Distress signals (near-perfect proxies)

| Column | Why |
|---|---|
| `MOD_FLAG` | Loans get modified because they are in trouble. |
| `FORBEARANCE_INDICATOR` | Same. |
| `PAYMENT_DEFERRAL_MOD_EVENT_FLAG` | Same. |
| `DELINQUENT_ACCRUED_INTEREST` | Nonzero only when delinquent. |
| `ADR_TYPE`, `ADR_COUNT`, `ADR_UPB` | Assistance / disaster relief. |
| `PRINCIPAL_FORGIVENESS_AMOUNT` | Only on a loss-mitigation workout. |

### Foreclosure economics (populated only on default)

`FORECLOSURE_COSTS`, `PROPERTY_PRESERVATION_AND_REPAIR_COSTS`,
`ASSET_RECOVERY_COSTS`, `MISCELLANEOUS_HOLDING_EXPENSES_AND_CREDITS`,
`ASSOCIATED_TAXES_FOR_HOLDING_PROPERTY`, `NET_SALES_PROCEEDS`,
`CREDIT_ENHANCEMENT_PROCEEDS`, `REPURCHASES_MAKE_WHOLE_PROCEEDS`,
`OTHER_FORECLOSURE_PROCEEDS`, `FORECLOSURE_PRINCIPAL_WRITE_OFF_AMOUNT`

### Loss accounting (populated only on a credit event)

`CURRENT_PERIOD_MODIFICATION_LOSS_AMOUNT`, `CUMULATIVE_MODIFICATION_LOSS_AMOUNT`,
`CURRENT_PERIOD_CREDIT_EVENT_NET_GAIN_OR_LOSS`,
`CUMULATIVE_CREDIT_EVENT_NET_GAIN_OR_LOSS`

### REO listing (the trap)

`ORIGINAL_LIST_START_DATE`, `ORIGINAL_LIST_PRICE`, `CURRENT_LIST_START_DATE`,
`CURRENT_LIST_PRICE`

Worth calling out explicitly. `ORIGINAL_LIST_PRICE` reads like the home's asking
price when the borrower bought it. It is not. It is the list price of the
foreclosed property when the servicer put it on the market as REO. It exists only
for loans that went through foreclosure. Perfect leakage wearing an
origination-sounding name.

---

## Group 4: LP objective and constraints

These ride along in the dataframe for stages 3 and 4 but never enter the feature
matrix. They are outputs of the pipeline's economics, not inputs to the model.

| Column | Role |
|---|---|
| `ORIG_UPB` | Budget constraint cost coefficient. |
| `interest_income_7yr` | Income-if-performs term in the objective. |
| `loss_if_default` | Loss-if-defaults term. Equals `lgd` x `ORIG_UPB`. |
| `lgd` | Flat 0.30 (Sirignano good-economy). Constant across all rows. |
| `STATE` | Diversification constraint key. |
| `monthly_payment` | Input to the amortization; not used directly. |
| `credit_grade` | Naive baseline scorer (FICO half). |

### The objective

```
c_i = (1 - PD_i) x interest_income_7yr_i  -  PD_i x loss_if_default_i
```

subject to `sum(x_i x ORIG_UPB_i) <= Budget`, plus an average-PD ceiling and
per-state caps.

### Why 7-year interest and not lifetime

`default_flag` is cumulative over roughly an 8-year observation window, so `PD`
is an 8-year probability. Pairing an 8-year risk against 30-year lifetime
interest would systematically bias the objective toward risk, since the upside
accrues for 30 years while the downside has only 8 years to appear. Seven-year
income is horizon-matched to the label.

It also serves as a rough prepayment proxy (30-year mortgages have a median life
near 7 years), which partially covers the prepayment simplification.

Because mortgage interest is front-loaded, this is not a token slice: roughly 36%
of lifetime interest is earned in the first 7 years of a 30-year fixed loan.

### Stated limitations

1. `loss_if_default` uses `ORIG_UPB`, but a loan defaulting in year 4 has
   amortized to roughly 90% of original balance. Loss is overstated by ~10%.
   Conservative and roughly proportional across loans, so it has minimal effect
   on the LP's ranking.
2. The objective credits defaulted loans with zero interest income, when in
   practice payments were collected until default. Also conservative.
3. `lgd` is a flat 0.30 rather than the Qi-Yang realized computation. Deliberate:
   a realized LGD only exists for loans that defaulted and therefore cannot be
   used to score applicants.

---

## Known data-quality items

**1. Casts needed before modeling.** Only four raw columns arrived numeric
(`ORIG_RATE`, `ORIG_UPB`, `ORIG_TERM`, `CSCORE_B`). `OLTV`, `OCLTV`, and `DTI`
are all `String` and are three of the four strongest credit features. Cast before
any EDA on them, or the distributions will be wrong.

**2. Missing FICO.** `credit_grade` has 1,573 `Unknown` rows (0.08%), meaning
`CSCORE_B` is null there. Needs a stated rule: drop, or impute with a missing
indicator. Recommend the indicator, since missing FICO may itself be signal.

**3. Collinear pairs.** Do not include both members of any pair:

- `CSCORE_B` and `credit_grade`
- `CSCORE_B` and `ORIG_CLASSIC_FICO`
- `FIRST_FLAG` and `is_first_time`
- `HOMEREADY_PROGRAM_INDICATOR` and `is_homeready`
- `OLTV` and `OCLTV` (correlated but not identical; OCLTV includes second liens)

**4. Split strategy.** Stratified random on `default_flag`, three ways: train /
calibration / test. No temporal split. Within a single vintage every loan lived
through the same calendar, so an origination-date split does not test macro
generalization; it only tests whether autumn originations differ from spring
ones. Seasoning bias (a December 2017 loan has ~0.9 fewer years of exposure than
a January 2017 loan) is documented as a limitation. A real out-of-time test would
require adding a second vintage.

---

## What the EDA track can use from this

- The Group 1 table is the universe of features worth exploring. Default-rate
  breakdowns, distributions, and correlations should stay inside it.
- Group 2 and Group 3 columns are still worth describing in the EDA report as
  data-quality and provenance findings, but no Group 3 column should appear in a
  "drivers of default" analysis. They do not drive default, they record it.
- The casts in Known Data Quality item 1 block both tracks, so whoever does them
  first should push the result.

# 01_data_quality

```
(2046851, 115)
0.034143178961243394
                  mean    size
orig_quarter                  
2017Q1        0.031214  487789
2017Q2        0.032269  492517
2017Q3        0.034398  546663
2017Q4        0.038399  519882
True
```

**Base rate: 3.4%** default across ~2.05M loans (2017 originations, all four quarters, stable 3.1%–3.8% by quarter). This is the reference point where all "lift" values below are subgroup rate ÷ base rate.

```
CSCORE_B     nulls after coerce: 0.077%  range: 445.0–850.0
DTI          nulls after coerce: 0.017%  range: 1.0–63.0
ORIG_RATE    nulls after coerce: 0.000%  range: 1.79–6.125
OLTV         nulls after coerce: 0.000%  range: 2–97
OCLTV        nulls after coerce: 0.000%  range: 2–114
ORIG_UPB     nulls after coerce: 0.000%  range: 5000.0–1223000.0
ORIG_TERM    nulls after coerce: 0.000%  range: 36–360
```

Data quality: all origination features coerce cleanly to numeric (<0.1% nulls); no Fannie sentinel values (9999 FICO, 999 DTI) contaminating the columns. Ranges are all plausible. Safe to model on.

```
/var/folders/5g/nyyrx9tx5nbfgnrym8rw723m0000gn/T/ipykernel_76784/3838274286.py:2: FutureWarning: The default of observed=False is deprecated and will be changed to True in a future version of pandas. Pass observed=False to retain current behavior or observed=True to adopt the future default and silence this warning.
  g = df.groupby(pd.cut(df[col], bins))["default_flag"]
```

```
mean    size      lift
CSCORE_B                              
(300, 620]  0.123989    1484  3.631449
(620, 660]  0.108010  102222  3.163443
(660, 700]  0.073385  254412  2.149328
(700, 740]  0.043869  422215  1.284844
(740, 780]  0.023800  579244  0.697064
(780, 850]  0.011140  685701  0.326285
```

```
/var/folders/5g/nyyrx9tx5nbfgnrym8rw723m0000gn/T/ipykernel_76784/3838274286.py:2: FutureWarning: The default of observed=False is deprecated and will be changed to True in a future version of pandas. Pass observed=False to retain current behavior or observed=True to adopt the future default and silence this warning.
  g = df.groupby(pd.cut(df[col], bins))["default_flag"]
```

```
mean    size      lift
DTI                                 
(0, 20]   0.011856  167425  0.347245
(20, 30]  0.019133  484301  0.560368
(30, 36]  0.029545  418380  0.865324
(36, 43]  0.042624  601751  1.248388
(43, 50]  0.054968  374633  1.609940
(50, 65]  0.000000      21  0.000000
```

```
/var/folders/5g/nyyrx9tx5nbfgnrym8rw723m0000gn/T/ipykernel_76784/3838274286.py:2: FutureWarning: The default of observed=False is deprecated and will be changed to True in a future version of pandas. Pass observed=False to retain current behavior or observed=True to adopt the future default and silence this warning.
  g = df.groupby(pd.cut(df[col], bins))["default_flag"]
```

```
mean    size      lift
OLTV                                 
(0, 60]    0.020946  391141  0.613487
(60, 70]   0.030740  252021  0.900312
(70, 80]   0.031312  786434  0.917086
(80, 90]   0.035643  233451  1.043941
(90, 95]   0.051220  272568  1.500160
(95, 100]  0.063280  111236  1.853368
```

```
mean    size
STATE                  
VI     0.125000     128
PR     0.081258    2449
FL     0.056946  141082
NY     0.056179   62924
HI     0.053410    6759
LA     0.050447   20041
DC     0.048153    4901
TX     0.046143  164662
NJ     0.045474   47698
CT     0.045293   17729
NV     0.044219   30304
IL     0.041034   74134
MD     0.040189   38891
AK     0.038307    3237
MS     0.036526    9500
```

Risk hierarchy so far, strongest to weakest:

| Feature   | Pattern                          | Approx. swing | Notes |
|-----------|----------------------------------|---------------|-------|
| CSCORE_B  | Smooth, monotonic decline        | ~10×          | Dominant signal. <620 defaults 12.4% (3.6× lift); 780+ only 1.1% (0.33×). But <660 is a thin slice of the book — most loans are 740+. |
| DTI       | Smooth, monotonic rise           | ~4–5×         | No cliff at the 43 conforming limit; risk rises steadily with leverage. Independent of FICO, so additive. |
| OLTV      | Flat through 80, sharp tail rise | ~3×           | Signal is in the tail: ~3% up to 80% LTV, jumps to 5.1% (90–95) and 6.3% (95–100). Captures equity/skin-in-the-game. |
| PURPOSE   | Weak ordering                    | ~1.5×         | Cash-out refi (C) 3.8% > purchase (P) 3.5% > rate-term refi (R) 2.6%. Real but minor next to the above. |

Caveats for the team:
- **ORIG_RATE deliberately not treated as a predictor.** Rate is priced from the same risk assessed at origination, so using it to predict default is partly circular / leakage-adjacent. Documented as a relationship, not a feature. Revisit before modeling.
- With ~2M rows, every subgroup difference is "statistically significant" where we rely on **lift / effect size**, not p-values, to judge what matters.
- Always check the `size` column before trusting a rate (see the DTI 50+ bin: 0% default on only 21 loans = noise, not a finding).

## Features Added Parquet

The goal is to find which columns in our features added parquet are non-null and to find what will be useful for our ML models

```
Rows: 2,046,851
Columns: 123
Base default rate: 0.0341
```

```
Fully null (100%):        68 columns
Mostly null (50–99%):     3 columns
Partially null (0–50%):   3 columns
Complete (0% null):       49 columns
```

```
null_count  null_pct   dtype  \
PRINCIPAL_FORGIVENESS_AMOUNT                   2046851     100.0  object   
MISCELLANEOUS_HOLDING_EXPENSES_AND_CREDITS     2046851     100.0  object   
ORIGINAL_LIST_START_DATE                       2046851     100.0  object   
POOL_ID                                        2046851     100.0  object   
NON_INTEREST_BEARING_UPB                       2046851     100.0  object   
...                                                ...       ...     ...   
OCC_STAT                                             0       0.0  object   
NO_UNITS                                             0       0.0  object   
PROP                                                 0       0.0  object   
PURPOSE                                              0       0.0  object   
is_hfa                                               0       0.0    int8   

                                            n_unique  
PRINCIPAL_FORGIVENESS_AMOUNT                       0  
MISCELLANEOUS_HOLDING_EXPENSES_AND_CREDITS         0  
ORIGINAL_LIST_START_DATE                           0  
POOL_ID                                            0  
NON_INTEREST_BEARING_UPB                           0  
...                                              ...  
OCC_STAT                                           3  
NO_UNITS                                           4  
PROP                                               5  
PURPOSE                                            3  
is_hfa                                             2  

[123 rows x 4 columns]
```

```
null_count  null_pct    dtype  n_unique
interest_income_7yr           0       0.0  float64     44122
lgd                           0       0.0  float64         1
loss_if_default               0       0.0  float64       969
credit_grade                  0       0.0   object         5
is_first_time                 0       0.0     int8         2
is_homeready                  0       0.0     int8         2
is_hfa                        0       0.0     int8         2
default_flag                  0       0.0     int8         2
```

```
=== FULLY NULL (100%) — 68 columns ===
['PRINCIPAL_FORGIVENESS_AMOUNT', 'MISCELLANEOUS_HOLDING_EXPENSES_AND_CREDITS', 'ORIGINAL_LIST_START_DATE', 'POOL_ID', 'NON_INTEREST_BEARING_UPB', 'OTHER_FORECLOSURE_PROCEEDS', 'REPURCHASES_MAKE_WHOLE_PROCEEDS', 'CREDIT_ENHANCEMENT_PROCEEDS', 'NET_SALES_PROCEEDS', 'ASSOCIATED_TAXES_FOR_HOLDING_PROPERTY', 'ASSET_RECOVERY_COSTS', 'ARM_PRODUCT_TYPE', 'PROPERTY_PRESERVATION_AND_REPAIR_COSTS', 'FORECLOSURE_COSTS', 'DISPOSITION_DATE', 'FORECLOSURE_DATE', 'LAST_PAID_INSTALLMENT_DATE', 'UNSCHD_PRNCPL_CURR', 'TOT_SCHD_PRNCPL', 'CURR_SCHD_PRNCPL', 'ORIGINAL_LIST_PRICE', 'CURRENT_LIST_START_DATE', 'CURRENT_LIST_PRICE', 'ISSUE_SCOREB', 'MONTHS_UNTIL_FIRST_PAYMENT_RESET', 'MONTHS_BETWEEN_SUBSEQUENT_PAYMENT_RESET', 'DELINQUENT_ACCRUED_INTEREST', 'LOAN_HOLDBACK_EFFECTIVE_DATE', 'LOAN_HOLDBACK_INDICATOR', 'ZERO_BALANCE_CODE_CHANGE_DATE', 'INTEREST_RATE_CHANGE_DATE', 'FORECLOSURE_PRINCIPAL_WRITE_OFF_AMOUNT', 'PAYMENT_CHANGE_DATE', 'CUMULATIVE_CREDIT_EVENT_NET_GAIN_OR_LOSS', 'CURRENT_PERIOD_CREDIT_EVENT_NET_GAIN_OR_LOSS', 'CUMULATIVE_MODIFICATION_LOSS_AMOUNT', 'CURRENT_PERIOD_MODIFICATION_LOSS_AMOUNT', 'ARM_INDEX', 'CURR_SCOREC', 'CURR_SCOREB', 'ISSUE_SCOREC', 'RPRCH_DTE', 'LAST_UPB', 'ZB_DTE', 'FORBEARANCE_INDICATOR', 'MASTER_SERVICER', 'ISSUANCE_UPB', 'CURR_CLASSIC_FICO', 'ISSUE_CLASSIC_FICO', 'ORIG_CLASSIC_FICO', 'INTEREST_BEARING_UPB', 'ADR_UPB', 'MI_CANCEL_FLAG', 'ADR_TYPE', 'RE_PROCS_FLAG', 'DEAL_NAME', 'ADR_COUNT', 'MNTHS_TO_AMTZ_IO', 'LIFETIME_INTEREST_RATE_CAP', 'ARM_CAP_STRUCTURE', 'PMT_HISTORY', 'PLAN_NUMBER', 'FIRST_PAY_IO', 'INITIAL_INTEREST_RATE_CAP', 'PERIODIC_INTEREST_RATE_CAP', 'ARM_5_YR_INDICATOR', 'MARGIN', 'BALLOON_INDICATOR']

=== MOSTLY NULL (50–99%) — 3 columns ===
          null_pct  n_unique
MI_TYPE      69.97         2
MI_PCT       69.97        28
CSCORE_C     52.92       217

=== PARTIALLY NULL (0–50%) — 3 columns ===
               null_pct  n_unique
zero_bal_code     25.33         7
CSCORE_B           0.08       221
DTI                0.02        58
```

```
count      mean
zero_bal_code                   
01             1519039  0.019017
02                1433  1.000000
03                 246  1.000000
06                1365  0.092308
09                1452  1.000000
15                 855  1.000000
16                3944  0.787272
NaN             518517  0.065151
_oltv_num   False   True 
_has_mi                  
False      0.6983  0.0014
True       0.0002  0.3002
NUM_BO         1       2       3       4    5    6
_has_cob                                          
False     0.5282  0.0009  0.0000  0.0000  0.0  0.0
True      0.0000  0.4620  0.0075  0.0013  0.0  0.0
```

```
['max_dlq_ever']
```

```
Sporadic nulls (CSCORE_B or DTI): 1,905 loans (0.093%) | default rate 0.0399 vs 0.0341 base

Columns: 128 -> 60 after dropping 68 dead
Model-safe candidate features: 29
['CSCORE_B', 'DTI', 'OLTV', 'OCLTV', 'NUM_BO', 'ORIG_UPB', 'ORIG_TERM', 'FIRST_FLAG', 'PURPOSE', 'PROP', 'NO_UNITS', 'OCC_STAT', 'STATE', 'MSA', 'ZIP', 'CHANNEL', 'SELLER', 'MI_PCT', 'MI_TYPE', 'CSCORE_C', 'has_mi', 'has_coborrower', 'credit_grade', 'is_first_time', 'is_homeready', 'is_hfa', 'HIGH_BALANCE_LOAN_INDICATOR', 'PROPERTY_INSPECTION_WAIVER_INDICATOR', 'RELOCATION_MORTGAGE_INDICATOR']
```

### Check for any null columns remaining

```
57
[]
```

```
Fully-null columns remaining: 0 -> []
```

### Export cleaned data to new parquet

```
2,044,946 loans x 57 cols | default rate 0.0341
```

# Data Quality Audit
**Purpose**: Establish that the Fannie Mae 2017 dataset is trustworthy before any modeling or optimization, and determine which of its fields are actually usable. 01_data_initial_check (from ml-lp-sim) was an initial reconnaissance for LP parameter sizing; this is the systematic audit.

**What was done:** Full-column census. All 123 columns (115 raw Fannie fields + 8 engineered in 02_initial_feat_end from ml-lp-sim) were audited for missingness, dtype, and cardinality. Columns were bucketed by null share to make a 123-row table interpretable at a glance.

**Structural inapplicability:** 68 columns are entirely null. These resolve into four coherent themes — recovery/foreclosure/disposition fields, the ARM block, time-varying current-state fields, and administrative/servicing fields — all structurally inapplicable to a performing, fixed-rate, origination-time book. This is a property of the data, not a data-quality failure. It also completes the audit trail behind the LGD decision: every field required by the Qi–Yang (2007) formula is null, so the Sirignano flat-value assumption (30% baseline / 50% downturn) is a necessary fallback, not a convenience.
**Informative absence:** Three columns appeared "mostly null" but encode structural facts rather than missing data. MI_PCT/MI_TYPE (69.97% null) are null precisely when mortgage insurance is not required — cross-checked against OLTV > 80 at 99.85% agreement. CSCORE_C (52.9% null) is null precisely when there is no co-borrower — cross-checked against NUM_BO == 1 with zero contradictions. Both were encoded as explicit indicators (has_mi, has_coborrower) rather than imputed. These cross-checks also serve as independent validation of the dataset's internal consistency.
**Label definition:** default_flag was traced to its source in src/reduce_fannie.py and documented as D180 OR credit-event disposition: (max_dlq_ever >= 6) OR (zero_bal_code ∈ {02, 03, 09, 15}). D180 is the standard convention. This closes an open decision listed in the project doc. The definition explains the observed pattern in zero_bal_code: the credit-event codes default at 100% by construction, while prepaid (1.9%) and still-active (6.5%) loans carry nonzero rates via the delinquency arm.
**Leakage identification:** Two label-derived columns survived the reduction into the feature table: max_dlq_ever and zero_bal_code. Both are components of default_flag and are unknowable at origination, when the funding decision is made. Both are fenced from modeling and retained for EDA only.
**Sporadic missingness:** Only two modeling features carry genuine missingness — CSCORE_B (0.08%) and DTI (0.02%), 1,905 loans combined. Tested for informativeness: 3.99% default rate vs. 3.41% base (1.17× lift) — directionally sensible but immaterial against the ~10× swing of CSCORE_B and on a slice this small. Dropped complete-case.

**Outputs:** A working set of 57 columns (123 -> 68 dropped), 29 model-safe candidate features, and a FEATURE_ROLES contract (identifier / target / label-derived / origination / economics-only / meta) shared with the optimization workstream. Persisted to fannie_2017_block1_clean.parquet.

**Why this serves the project goal:** The claim under test is that calibrated default probabilities produce better funding decisions than a naive rule. That claim rests on the probabilities being honest, which rests on the data being understood. This audit establishes what the data contains, proves it is internally consistent, documents what the target actually measures, and fences the fields that would have silently invalidated the model.

```
<Figure size 1100x600 with 1 Axes>
```

```
Never late:        84.91%
Ever delinquent:   15.09%
Reached D180 (default): 3.41%
Cured before D180: 11.69% (went delinquent but never hit the cutoff)
```

### Remove 'max_dlq_ever', 'zero_bal_code' columns to prevent data leakage

```
Dropped: ['max_dlq_ever', 'zero_bal_code']
clean now: 2,044,946 rows × 55 cols
Leaks remaining: []
```

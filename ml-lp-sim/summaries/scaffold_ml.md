# scaffold_ml

```
LOAN_ID                             String
POOL_ID                             String
ACT_PERIOD                          String
CHANNEL                             String
SELLER                              String
SERVICER                            String
MASTER_SERVICER                     String
ORIG_RATE                           Float64
CURR_RATE                           String
ORIG_UPB                            Float64
ISSUANCE_UPB                        String
CURRENT_UPB                         String
ORIG_TERM                           Float64
ORIG_DATE                           String
FIRST_PAY                           String
LOAN_AGE                            String
REM_MONTHS                          String
ADJ_REM_MONTHS                      String
MATR_DT                             String
OLTV                                String
OCLTV                               String
NUM_BO                              String
DTI                                 String
CSCORE_B                            Int32
CSCORE_C                            String
FIRST_FLAG                          String
PURPOSE                             String
PROP                                String
NO_UNITS                            String
OCC_STAT                            String
STATE                               String
MSA                                 String
ZIP                                 String
MI_PCT                              String
PRODUCT                             String
PPMT_FLG                            String
IO                                  String
FIRST_PAY_IO                        String
MNTHS_TO_AMTZ_IO                    String
PMT_HISTORY                         String
MOD_FLAG                            String
MI_CANCEL_FLAG                      String
ZB_DTE                              String
LAST_UPB                            String
RPRCH_DTE                           String
CURR_SCHD_PRNCPL                    String
TOT_SCHD_PRNCPL                     String
UNSCHD_PRNCPL_CURR                  String
LAST_PAID_INSTALLMENT_DATE          String
FORECLOSURE_DATE                    String
DISPOSITION_DATE                    String
FORECLOSURE_COSTS                   String
PROPERTY_PRESERVATION_AND_REPAIR_COSTS String
ASSET_RECOVERY_COSTS                String
MISCELLANEOUS_HOLDING_EXPENSES_AND_CREDITS String
ASSOCIATED_TAXES_FOR_HOLDING_PROPERTY String
NET_SALES_PROCEEDS                  String
CREDIT_ENHANCEMENT_PROCEEDS         String
REPURCHASES_MAKE_WHOLE_PROCEEDS     String
OTHER_FORECLOSURE_PROCEEDS          String
NON_INTEREST_BEARING_UPB            String
PRINCIPAL_FORGIVENESS_AMOUNT        String
ORIGINAL_LIST_START_DATE            String
ORIGINAL_LIST_PRICE                 String
CURRENT_LIST_START_DATE             String
CURRENT_LIST_PRICE                  String
ISSUE_SCOREB                        String
ISSUE_SCOREC                        String
CURR_SCOREB                         String
CURR_SCOREC        
... [truncated]
```

## Inspect string columns before casting

**What**
- Print sample values, null counts, and unparseable values for the 7 text columns that should be numeric.
- Read-only. Writes nothing, changes nothing.

**Why**
- `OLTV`, `OCLTV`, `DTI`, and 4 others are stored as text, not numbers. Cannot be averaged, plotted, sorted, or modeled until fixed.
- `.cast(pl.Float64)` fails silently on junk values like `""` or `"N/A"`. It does not error, it returns null. A blind cast can quietly delete data and we would not find out until model results look wrong.
- This step finds the junk first so the cast in Step 2 is deliberate.

**What to look for**
- Block 3 is the decision point. Empty lists for every column means the cast is safe and Step 2 is a one-liner.
- Non-empty means we need an explicit cleaning rule per column before casting.

```
--- sample values ---
shape: (8, 7)
┌──────┬───────┬─────┬──────────┬────────┬──────────┬────────┐
│ OLTV ┆ OCLTV ┆ DTI ┆ CSCORE_C ┆ NUM_BO ┆ NO_UNITS ┆ MI_PCT │
│ ---  ┆ ---   ┆ --- ┆ ---      ┆ ---    ┆ ---      ┆ ---    │
│ str  ┆ str   ┆ str ┆ str      ┆ str    ┆ str      ┆ str    │
╞══════╪═══════╪═════╪══════════╪════════╪══════════╪════════╡
│ 97   ┆ 97    ┆ 39  ┆ null     ┆ 1      ┆ 1        ┆ 25.00  │
│ 41   ┆ 41    ┆ 19  ┆ null     ┆ 1      ┆ 1        ┆ null   │
│ 78   ┆ 78    ┆ 41  ┆ 800      ┆ 2      ┆ 1        ┆ null   │
│ 67   ┆ 67    ┆ 29  ┆ 774      ┆ 2      ┆ 1        ┆ null   │
│ 75   ┆ 75    ┆ 44  ┆ 689      ┆ 2      ┆ 1        ┆ null   │
│ 80   ┆ 80    ┆ 31  ┆ null     ┆ 1      ┆ 1        ┆ null   │
│ 95   ┆ 95    ┆ 25  ┆ 779      ┆ 2      ┆ 1        ┆ 30.00  │
│ 54   ┆ 54    ┆ 30  ┆ 723      ┆ 2      ┆ 1        ┆ null   │
└──────┴───────┴─────┴──────────┴────────┴──────────┴────────┘

--- null counts (as String) ---
shape: (1, 7)
┌──────┬───────┬─────┬──────────┬────────┬──────────┬─────────┐
│ OLTV ┆ OCLTV ┆ DTI ┆ CSCORE_C ┆ NUM_BO ┆ NO_UNITS ┆ MI_PCT  │
│ ---  ┆ ---   ┆ --- ┆ ---      ┆ ---    ┆ ---      ┆ ---     │
│ u32  ┆ u32   ┆ u32 ┆ u32      ┆ u32    ┆ u32      ┆ u32     │
╞══════╪═══════╪═════╪══════════╪════════╪══════════╪═════════╡
│ 0    ┆ 0     ┆ 340 ┆ 1083143  ┆ 0      ┆ 0        ┆ 1432111 │
└──────┴───────┴─────┴──────────┴────────┴──────────┴─────────┘

--- values that will NOT cast to Float64 ---
OLTV       0 distinct bad values shown: []
OCLTV      0 distinct bad values shown: []
DTI        0 distinct bad values shown: []
CSCORE_C   0 distinct bad values shown: []
NUM_BO     0 distinct bad values shown: []
NO_UNITS   0 distinct bad values shown: []
MI_PCT     0 distinct bad values shown: []
```

## Cast types and write the typed file

**What**
- Cast the 7 verified-clean text columns to numeric.
- Write a new file: `fannie_2017_typed.parquet`. The source file is untouched.

**Why**
- Types only. No fills, no drops, no new columns.
- Semantic fills (`MI_PCT` null to 0, etc.) belong in feature prep as code, not baked into a file. The EDA track may want to see nulls as nulls to identify which loans carry no MI.
- Keeping this to one job means if something breaks later we know it was not the cast.

**Verification built in**
- Null counts must be unchanged. If nulls went up, the cast silently ate data.
- Min/max on each column. Fannie uses sentinel codes (e.g. 999) in some fields; a max of 999 on DTI means we have a fake value pretending to be real.

```
--- rows ---
2046851

--- null counts after cast (must be unchanged) ---
shape: (1, 7)
┌──────┬───────┬─────┬──────────┬────────┬──────────┬─────────┐
│ OLTV ┆ OCLTV ┆ DTI ┆ CSCORE_C ┆ NUM_BO ┆ NO_UNITS ┆ MI_PCT  │
│ ---  ┆ ---   ┆ --- ┆ ---      ┆ ---    ┆ ---      ┆ ---     │
│ u32  ┆ u32   ┆ u32 ┆ u32      ┆ u32    ┆ u32      ┆ u32     │
╞══════╪═══════╪═════╪══════════╪════════╪══════════╪═════════╡
│ 0    ┆ 0     ┆ 340 ┆ 1083143  ┆ 0      ┆ 0        ┆ 1432111 │
└──────┴───────┴─────┴──────────┴────────┴──────────┴─────────┘

--- ranges (watch for sentinel values) ---
shape: (14, 2)
┌──────────────┬──────────┐
│ column       ┆ column_0 │
│ ---          ┆ ---      │
│ str          ┆ f64      │
╞══════════════╪══════════╡
│ OLTV_min     ┆ 2.0      │
│ OCLTV_min    ┆ 2.0      │
│ DTI_min      ┆ 1.0      │
│ CSCORE_C_min ┆ 620.0    │
│ NUM_BO_min   ┆ 1.0      │
│ …            ┆ …        │
│ DTI_max      ┆ 63.0     │
│ CSCORE_C_max ┆ 839.0    │
│ NUM_BO_max   ┆ 6.0      │
│ NO_UNITS_max ┆ 4.0      │
│ MI_PCT_max   ┆ 40.0     │
└──────────────┴──────────┘
```

## Re-display ranges without truncation

**What**
- Same min/max check, forced to print all 14 rows.
- Plus a count of `OLTV` above 100.

**Why**
- Default Polars display collapsed the middle rows. `OLTV_max` was in the collapsed block.
- `OLTV` is where a sentinel would hide. Standard Fannie caps around 97, some programs reach 105. A max of 999 means a fake value in our strongest LTV feature.
- The `OLTV > 100` count separates "a few legitimate high-LTV program loans" from "a block of sentinels."

```
shape: (14, 2)
┌──────────────┬──────────┐
│ column       ┆ column_0 │
│ ---          ┆ ---      │
│ str          ┆ f64      │
╞══════════════╪══════════╡
│ OLTV_min     ┆ 2.0      │
│ OCLTV_min    ┆ 2.0      │
│ DTI_min      ┆ 1.0      │
│ CSCORE_C_min ┆ 620.0    │
│ NUM_BO_min   ┆ 1.0      │
│ NO_UNITS_min ┆ 1.0      │
│ MI_PCT_min   ┆ 6.0      │
│ OLTV_max     ┆ 97.0     │
│ OCLTV_max    ┆ 114.0    │
│ DTI_max      ┆ 63.0     │
│ CSCORE_C_max ┆ 839.0    │
│ NUM_BO_max   ┆ 6.0      │
│ NO_UNITS_max ┆ 4.0      │
│ MI_PCT_max   ┆ 40.0     │
└──────────────┴──────────┘

--- OLTV above 100 ---
shape: (1, 2)
┌─────┬──────┐
│ n   ┆ max  │
│ --- ┆ ---  │
│ u32 ┆ f64  │
╞═════╪══════╡
│ 0   ┆ null │
└─────┴──────┘
```

## Assign the split in memory

**What**
- Collect the ~34 admissible + LP columns from the typed file into `df`.
- Add a `split` column via `hash(LOAN_ID) % 100`: 0-59 train, 60-79 calib, 80-99 test.
- No new parquet. `df` lives in the session.

**Why no file**
- The split is deterministic from `LOAN_ID`. Any teammate reruns this cell and gets identical splits. Nothing to persist.
- Writing 2M rows on every iteration was the bottleneck, and it bought nothing.

**Why hash instead of shuffle**
- Same loan lands in the same split every run, on every machine, with no stored seed.
- Pure column math. No shuffle, no window, no join.

**Not exactly stratified, and that's fine**
- Random assignment drifts the test default rate by roughly ±0.03%.
- Invisible to AUC and calibration. Verified empirically below instead of guaranteed structurally.

**Timers**
- Each step is timed. If something is slow we will know which line instead of guessing.

```
collect      :    0.0s   shape=(2046851, 35)
split assign :    0.0s

--- split sizes and default rate ---
shape: (3, 4)
┌───────┬─────────┬───────────┬──────────────┐
│ split ┆ n       ┆ positives ┆ default_rate │
│ ---   ┆ ---     ┆ ---       ┆ ---          │
│ str   ┆ u32     ┆ i64       ┆ f64          │
╞═══════╪═════════╪═══════════╪══════════════╡
│ calib ┆ 409353  ┆ 14094     ┆ 0.03443      │
│ test  ┆ 409926  ┆ 13982     ┆ 0.034109     │
│ train ┆ 1227572 ┆ 41810     ┆ 0.034059     │
└───────┴─────────┴───────────┴──────────────┘

split nulls: 0   memory: 319 MB
```

## Synthetic PD generator

**What**
- Produce a fake but plausible `pd` per loan for the test split.
- Emit the exact schema the real model will emit, so swapping in week 6 is a one-line change.

**Why now**
- The LP and Monte Carlo need a PD column, not a good PD column. Waiting for the real model blocks stages 3 and 4 for weeks.
- This is the data contract from the launch report, made concrete. Lock the schema now and the LP never has to change.

**Why build it from real FICO / OLTV / DTI instead of random draws**
- The LP's average-PD ceiling and state caps interact with *which* loans are risky. Random PDs would scatter risk uniformly across states and FICO bands, so the constraints would behave nothing like they will on real PDs.
- Built from real features, risky loans cluster where they actually cluster. The LP prototype behaves like the real thing.
- Free side effect: it has genuine signal against `default_flag`, so we can sanity-check with AUC.

**Method**
- Logistic function on standardized FICO, OLTV, DTI, plus noise.
- Coefficients are hand-set to mortgage-plausible signs and magnitudes. FICO dominant and negative, LTV and DTI positive.
- Intercept solved numerically so mean PD lands on the observed 3.4143%.

**Throwaway.** No tuning, no validation. It exists to be deleted.

```
--- contract schema (what the LP consumes) ---
  LOAN_ID                String
  ORIG_UPB               Float64
  interest_income_7yr    Float64
  loss_if_default        Float64
  STATE                  String
  credit_grade           String
  default_flag           Int8
  pd                     Float64

rows        : 409,926
mean pd     : 0.034143   (target 0.034143)
actual rate : 0.034109

--- pd distribution ---
shape: (9, 2)
┌────────────┬──────────┐
│ statistic  ┆ value    │
│ ---        ┆ ---      │
│ str        ┆ f64      │
╞════════════╪══════════╡
│ count      ┆ 409926.0 │
│ null_count ┆ 0.0      │
│ mean       ┆ 0.034143 │
│ std        ┆ 0.045098 │
│ min        ┆ 0.000188 │
│ 25%        ┆ 0.007781 │
│ 50%        ┆ 0.017309 │
│ 75%        ┆ 0.041353 │
│ max        ┆ 0.565142 │
└────────────┴──────────┘

synthetic AUC vs real default_flag: 0.7178
```

## Inspect categoricals before encoding

**What**
- Cardinality, nulls, and value counts for the 14 categorical columns.
- Read-only.

**Why**
- Same discipline as inspecting strings before casting. Encode blind and you get silent damage.
- `SELLER` is the known problem. Fannie has hundreds of sellers with a long tail of tiny ones. One-hot on raw `SELLER` would add hundreds of columns, most firing on a handful of loans each, and LogReg would happily overfit them.
- Constant columns waste space and confuse coefficient interpretation. `PRODUCT` is likely constant on a 2017 fixed-rate book.
- LogReg needs one-hot. XGBoost and LightGBM take categoricals natively. The encoding plan depends on what is actually in here.

**What to look for**
- Any column with `n_unique = 1` gets dropped.
- `SELLER` cardinality decides whether we group the tail or drop it.
- Nulls in categoricals need a rule, same as the numerics.

```
--- cardinality and nulls ---
shape: (14, 3)
┌─────────────────────────────────┬──────────┬───────┐
│ column                          ┆ n_unique ┆ nulls │
│ ---                             ┆ ---      ┆ ---   │
│ str                             ┆ u32      ┆ u32   │
╞═════════════════════════════════╪══════════╪═══════╡
│ STATE                           ┆ 54       ┆ 0     │
│ SELLER                          ┆ 38       ┆ 0     │
│ PROP                            ┆ 5        ┆ 0     │
│ PROPERTY_INSPECTION_WAIVER_IND… ┆ 4        ┆ 0     │
│ CHANNEL                         ┆ 3        ┆ 0     │
│ …                               ┆ …        ┆ …     │
│ IO                              ┆ 2        ┆ 1     │
│ HIGH_BALANCE_LOAN_INDICATOR     ┆ 2        ┆ 0     │
│ RELOCATION_MORTGAGE_INDICATOR   ┆ 2        ┆ 0     │
│ PRODUCT                         ┆ 1        ┆ 0     │
│ PPMT_FLG                        ┆ 1        ┆ 0     │
└─────────────────────────────────┴──────────┴───────┘

--- value counts for low-cardinality columns ---

CHANNEL  (k=3)
shape: (3, 2)
┌─────────┬─────────┐
│ CHANNEL ┆ count   │
│ ---     ┆ ---     │
│ str     ┆ u32     │
╞═════════╪═════════╡
│ R       ┆ 1189241 │
│ C       ┆ 672737  │
│ B       ┆ 184873  │
└─────────┴─────────┘

PURPOSE  (k=3)
shape: (3, 2)
┌─────────┬─────────┐
│ PURPOSE ┆ count   │
│ ---     ┆ ---     │
│ str     ┆ u32     │
╞═════════╪═════════╡
│ P       ┆ 1163208 │
│ C       ┆ 485468  │
│ R       ┆ 398175  │
└─────────┴─────────┘

PROP  (k=5)
shape: (5, 2)
┌──────┬─────────┐
│ PROP ┆ count   │
│ ---  ┆ ---     │
│ str  ┆ u32     │
╞══════╪═════════╡
│ SF   ┆ 1258954 │
│ PU   ┆ 560917  │
│ CO   ┆ 200395  │
│ MH   ┆ 17139   │
│ CP   ┆ 9446    │
└──────┴─────────┘

OCC_STAT  (k=3)
shape: (3, 2)
┌──────────┬─────────┐
│ OCC_STAT ┆ count   │
│ ---      ┆ ---     │
│ str      ┆ u32     │
╞══════════╪═════════╡
│ P        ┆ 1790115 │
│ I        ┆ 163179  │
│ S        ┆ 93557   │
└──────────┴─────────┘

PRODUCT  (k=1)
shape: (1, 2)
┌─────────┬─────────┐
│ PRODUCT ┆ count   │
│ ---     ┆ ---     │
│ str     ┆ u32     │
╞═════════╪═════════╡
│ FRM     ┆ 2046851 │
└─────────┴─────────┘

MI_TYPE  (k=3)
shape: (3, 2)
┌─────────┬─────────┐
│ MI_TYPE ┆ count   │
│ ---     ┆ ---     │
│ str     ┆ u32     │
╞═════════╪═════════╡
│ null    ┆ 1432111 │
│ 1       ┆ 542264  │
│ 2       ┆ 72476   │
└─────────┴─────────┘

FIRST_FLAG  (k=2)
shape: (2, 2)
┌────────────┬─────────┐
│ FIRST_FLAG ┆ count   │
│ ---        ┆ ---     │
│ str        ┆ u32     │
╞════════════╪═════════╡
│ N          ┆ 1558365 │
│ Y          ┆ 488486  │
└────────────┴─────────┘

PPMT_FLG  (k=1)
shape: (1, 2)
┌──────────┬─────────┐
│ PPMT_FLG ┆ count   │
│ ---      ┆ ---     │
│ str      ┆ u32     │
╞══════════╪═════════╡
│ N        ┆ 2046851 │
└──────────┴─────────┘

IO  (k=2)
shape: (2, 2)
┌──────┬─────────┐
│ IO   ┆ count   │
│ ---  ┆ ---     │
│ str  ┆ u32     │
╞══════╪═════════╡
│ N    ┆ 2046850 │
│ null ┆ 1       │
└──────┴─────────┘

HIGH_BALANCE_LOAN_INDICAT
... [truncated]
```

## Verify the duplicate pair and inspect SELLER

**What**
- Cross-tab `FIRST_FLAG` against `is_first_time` to confirm they are the same column.
- Default rate by `SELLER`, to see whether it carries signal and whether the Quicken entities behave alike.

**Why**
- Do not drop a column on the assumption it duplicates another. Verify, then drop.
- If the two Quicken entities have materially different default rates they may be different books despite the shared name, and merging would blur signal. If they match, merging is safe.
- If `SELLER` default rates are flat across the board, it earns no place in the model and 37 dummies go away.

```
--- FIRST_FLAG vs is_first_time ---
shape: (2, 3)
┌────────────┬───────────────┬─────────┐
│ FIRST_FLAG ┆ is_first_time ┆ len     │
│ ---        ┆ ---           ┆ ---     │
│ str        ┆ i8            ┆ u32     │
╞════════════╪═══════════════╪═════════╡
│ N          ┆ 0             ┆ 1558365 │
│ Y          ┆ 1             ┆ 488486  │
└────────────┴───────────────┴─────────┘

--- default rate by SELLER (n >= 20k) ---
shape: (18, 3)
┌─────────────────────────────────┬────────┬────────┐
│ SELLER                          ┆ n      ┆ rate   │
│ ---                             ┆ ---    ┆ ---    │
│ str                             ┆ u32    ┆ f64    │
╞═════════════════════════════════╪════════╪════════╡
│ U.S. Bank N.A.                  ┆ 45849  ┆ 0.0848 │
│ Loandepot.Com, Llc              ┆ 28345  ┆ 0.0461 │
│ Caliber Home Loans, Inc.        ┆ 24056  ┆ 0.0425 │
│ Flagstar Bank, Fsb              ┆ 40402  ┆ 0.0417 │
│ Wells Fargo Bank, N.A.          ┆ 309551 ┆ 0.0414 │
│ …                               ┆ …      ┆ …      │
│ Other                           ┆ 932204 ┆ 0.0302 │
│ Pennymac Corp.                  ┆ 23253  ┆ 0.0298 │
│ Fairway Independent Mortgage C… ┆ 25015  ┆ 0.0292 │
│ Franklin American Mortgage Com… ┆ 27207  ┆ 0.0228 │
│ Jpmorgan Chase Bank, National … ┆ 97682  ┆ 0.0221 │
└─────────────────────────────────┴────────┴────────┘
```

## Session display config

**What**
- Set Polars display once, globally, for the session.
- Run near the top of the notebook.

**Why**
- Polars collapses tables past ~10 rows and truncates strings past ~30 chars by default.
- We keep hitting it on 14-row, 38-row, 54-row tables and re-running to see the middle. `STATE` at 54 rows and `SELLER` at 38 would both truncate every time.
- Set once, never think about it again.

```
polars.config.Config
```

## SELLER: signal or proxy

**What**
- Full seller table, no truncation.
- Default rate alongside mean FICO, OLTV, DTI per seller.

**Why**
- A raw default rate by seller cannot distinguish worse underwriting from a riskier loan mix. Putting the credit characteristics next to the rate makes it visible by eye.
- Decides whether `SELLER` earns 37 dummies in LogReg or gets dropped as redundant with FICO and LTV.
- Also surfaces the two Quicken entities, which the default display collapsed.

```
shape: (18, 6)
┌───────────────────────────────────────────┬────────┬────────┬───────┬──────┬──────┐
│ SELLER                                    ┆ n      ┆ rate   ┆ fico  ┆ oltv ┆ dti  │
│ ---                                       ┆ ---    ┆ ---    ┆ ---   ┆ ---  ┆ ---  │
│ str                                       ┆ u32    ┆ f64    ┆ f64   ┆ f64  ┆ f64  │
╞═══════════════════════════════════════════╪════════╪════════╪═══════╪══════╪══════╡
│ U.S. Bank N.A.                            ┆ 45849  ┆ 0.0848 ┆ 739.0 ┆ 84.8 ┆ 35.6 │
│ Loandepot.Com, Llc                        ┆ 28345  ┆ 0.0461 ┆ 732.0 ┆ 70.7 ┆ 36.1 │
│ Caliber Home Loans, Inc.                  ┆ 24056  ┆ 0.0425 ┆ 741.0 ┆ 77.0 ┆ 35.4 │
│ Flagstar Bank, Fsb                        ┆ 40402  ┆ 0.0417 ┆ 747.0 ┆ 71.4 ┆ 35.0 │
│ Wells Fargo Bank, N.A.                    ┆ 309551 ┆ 0.0414 ┆ 753.0 ┆ 76.2 ┆ 34.9 │
│ Movement Mortgage, Llc                    ┆ 28701  ┆ 0.0383 ┆ 750.0 ┆ 81.5 ┆ 35.4 │
│ Nationstar Mortgage, Llc                  ┆ 26094  ┆ 0.0383 ┆ 737.0 ┆ 71.4 ┆ 35.3 │
│ Amerihome Mortgage Company, Llc           ┆ 33537  ┆ 0.0374 ┆ 746.0 ┆ 76.5 ┆ 35.8 │
│ United Shore Financial Services, Llc Dba… ┆ 49905  ┆ 0.0371 ┆ 757.0 ┆ 75.5 ┆ 36.1 │
│ Truist Bank (Formerly Suntrust Bank)      ┆ 45024  ┆ 0.0357 ┆ 757.0 ┆ 71.8 ┆ 34.0 │
│ Pmtt4                                     ┆ 53039  ┆ 0.0354 ┆ 754.0 ┆ 83.1 ┆ 35.7 │
│ Quicken Loans Inc.                        ┆ 36253  ┆ 0.0306 ┆ 741.0 ┆ 70.0 ┆ 34.0 │
│ Quicken Loans, Llc                        ┆ 119581 ┆ 0.0304 ┆ 740.0 ┆ 70.5 ┆ 34.9 │
│ Other                                     ┆ 932204 ┆ 0.0302 ┆ 750.0 ┆ 74.6 ┆ 34.0 │
│ Pennymac Corp.                            ┆ 23253  ┆ 0.0298 ┆ 756.0 ┆ 71.7 ┆ 34.1 │
│ Fairway Independent Mortgage Corporation  ┆ 25015  ┆ 0.0292 ┆ 752.0 ┆ 79.3 ┆ 34.8 │
│ Franklin American Mortgage Company        ┆ 27207  ┆ 0.0228 ┆ 753.0 ┆ 75.8 ┆ 33.1 │
│ Jpmorgan Chase Bank, National Associatio… ┆ 97682  ┆ 0.0221 ┆ 761.0 ┆ 71.6 ┆ 35.5 │
└───────────────────────────────────────────┴────────┴────────┴───────┴──────┴──────┘
```

## Finding: SELLER carries signal beyond loan characteristics

Default rates span 2.21% to 8.48% across 37 sellers. Book average is 3.41%.

Loan mix does not explain it:

| Seller | FICO | OLTV | DTI | Rate |
|---|---|---|---|---|
| U.S. Bank | 739 | 84.8 | 35.6 | 8.48% |
| Pmtt4 | 754 | 83.1 | 35.7 | 3.54% |
| Movement Mortgage | 750 | 81.5 | 35.4 | 3.83% |

Same LTV, same DTI, 15 FICO points apart, less than half the default rate. A
15-point FICO gap in the 740s moves risk 20-30%, not 140%.

**Effect:** `SELLER` stays as a feature. Cardinality is 38, not hundreds, because
Fannie pre-buckets small originators into `Other`. No tail grouping needed.
`Quicken Loans, Llc` and `Quicken Loans Inc.` are the same book (3.04% vs 3.06%,
FICO 740 vs 741) and were merged. 38 → 37.

**Two caveats.** `Other` is 932,204 loans, 45.5% of the book. It is Fannie's
catch-all, so the largest level means "unknown lender." And U.S. Bank is a named
public company: we can say its 2017 loans defaulted at 2.4x the book rate and
FICO/LTV/DTI do not explain it. We cannot say anything about its underwriting.
One vintage, and channel and geography are uncontrolled.

## Feature prep

**What**
- Drop constants and the confirmed duplicate.
- Merge the two Quicken entities.
- Apply the null rules.
- Emit `X_num`, `X_cat`, and the final feature lists.

**Drops**
- `PRODUCT`, `PPMT_FLG`, `IO`: zero variance. All-FRM book also confirms the ARM block is dead.
- `FIRST_FLAG`: verified duplicate of `is_first_time`. Keeping the Int8.
- `credit_grade`: reserved for the naive baseline scorer. Collinear with `CSCORE_B`.
- `orig_quarter`: origination-time and admissible, but we chose a random split deliberately. Feeding origination timing to the model invites it to learn the seasoning artifact we agreed to treat as a limitation. Held out.

**Null rules (closing the OPEN items in ml_data.md)**
- `MI_PCT` null to 0. Zero coverage is the true value. Verified: `MI_TYPE` nulls match `MI_PCT` nulls exactly at 1,432,111, so both are structural.
- `MI_TYPE` null to `"NONE"`. Same loans, same reason.
- `CSCORE_C` null to 0 plus `has_coborrower` indicator. There is no co-borrower score to estimate when there is no co-borrower. The indicator carries the meaning; the 0 is inert padding for the model.
- `CSCORE_B` null (1,573) to median plus `fico_missing` indicator. Missing FICO may itself be signal.
- `DTI` null (340) to median. 0.017% of rows. Too small for an indicator to be estimable.

**Not doing yet**
- No new features. `rep_fico = min(CSCORE_B, CSCORE_C)` and `second_lien = OCLTV - OLTV` stay parked until baselines exist.

**Verification built in**
- Variance check on every numeric. `ORIG_TERM` has not been checked and may be near-constant at 360.
- Null count after prep must be zero everywhere.

```
--- numeric variance (drop anything with n_unique = 1) ---
shape: (16, 2)
┌────────────────┬──────────┐
│ column         ┆ n_unique │
│ ---            ┆ ---      │
│ str            ┆ u32      │
╞════════════════╪══════════╡
│ is_first_time  ┆ 2        │
│ is_homeready   ┆ 2        │
│ is_hfa         ┆ 2        │
│ has_coborrower ┆ 2        │
│ fico_missing   ┆ 2        │
│ NO_UNITS       ┆ 4        │
│ NUM_BO         ┆ 6        │
│ MI_PCT         ┆ 29       │
│ DTI            ┆ 58       │
│ OLTV           ┆ 96       │
│ OCLTV          ┆ 112      │
│ CSCORE_C       ┆ 218      │
│ CSCORE_B       ┆ 221      │
│ ORIG_TERM      ┆ 235      │
│ ORIG_UPB       ┆ 969      │
│ ORIG_RATE      ┆ 2141     │
└────────────────┴──────────┘

--- nulls after prep (all must be 0) ---
shape: (0, 2)
┌────────┬───────┐
│ column ┆ nulls │
│ ---    ┆ ---   │
│ str    ┆ u32   │
╞════════╪═══════╡
└────────┴───────┘
(empty above = clean)

SELLER levels after merge: 37  (was 38)
features: 11 numeric + 5 flags + 10 categorical
shape: (2046851, 34)
```

## Check ORIG_TERM against the 7-year income window

**What**
- Distribution of `ORIG_TERM`, plus range.
- For loans with `ORIG_TERM < 84`, compare `interest_income_7yr` to total lifetime interest.

**Why**
- `interest_income_7yr` assumes an 84-month window. Loans shorter than that are paid off first.
- If the column was computed by running amortization to 84 months regardless of term, short loans are credited with interest on a zero balance. That inflates their objective coefficient and the LP would preferentially fund them.
- For a loan with term < 84, correct behavior is `interest_income_7yr` = full lifetime interest.

**The test**
- Lifetime interest = `monthly_payment` x `ORIG_TERM` - `ORIG_UPB`.
- If `interest_income_7yr` exceeds that for short-term loans, the column is wrong.

```
--- ORIG_TERM ---
shape: (9, 2)
┌────────────┬────────────┐
│ statistic  ┆ value      │
│ ---        ┆ ---        │
│ str        ┆ f64        │
╞════════════╪════════════╡
│ count      ┆ 2.046851e6 │
│ null_count ┆ 0.0        │
│ mean       ┆ 321.932509 │
│ std        ┆ 72.386825  │
│ min        ┆ 36.0       │
│ 25%        ┆ 360.0      │
│ 50%        ┆ 360.0      │
│ 75%        ┆ 360.0      │
│ max        ┆ 360.0      │
└────────────┴────────────┘
shape: (8, 2)
┌───────────┬─────────┐
│ ORIG_TERM ┆ count   │
│ ---       ┆ ---     │
│ f64       ┆ u32     │
╞═══════════╪═════════╡
│ 360.0     ┆ 1577778 │
│ 180.0     ┆ 302536  │
│ 240.0     ┆ 107811  │
│ 120.0     ┆ 34215   │
│ 300.0     ┆ 10886   │
│ 96.0      ┆ 1644    │
│ 144.0     ┆ 1343    │
│ 348.0     ┆ 980     │
└───────────┴─────────┘

loans with term < 84 months: 9
shape: (5, 5)
┌───────────┬──────────┬───────────┬─────────────────────┬───────────────────┐
│ ORIG_TERM ┆ ORIG_UPB ┆ ORIG_RATE ┆ interest_income_7yr ┆ lifetime_interest │
│ ---       ┆ ---      ┆ ---       ┆ ---                 ┆ ---               │
│ f64       ┆ f64      ┆ f64       ┆ f64                 ┆ f64               │
╞═══════════╪══════════╪═══════════╪═════════════════════╪═══════════════════╡
│ 72.0      ┆ 25000.0  ┆ 3.0       ┆ 2348.616475         ┆ 2349.0            │
│ 36.0      ┆ 60000.0  ┆ 4.25      ┆ 4012.30315          ┆ 4012.0            │
│ 60.0      ┆ 73000.0  ┆ 3.5       ┆ 6679.84297          ┆ 6680.0            │
│ 60.0      ┆ 60000.0  ┆ 3.375     ┆ 5288.951219         ┆ 5289.0            │
│ 60.0      ┆ 25000.0  ┆ 3.375     ┆ 2203.729675         ┆ 2204.0            │
└───────────┴──────────┴───────────┴─────────────────────┴───────────────────┘
```

## Default rate by loan term

**What**
- Default rate and mean FICO by `ORIG_TERM`, for the five terms with real mass.

**Why**
- Confirms whether `ORIG_TERM` carries signal or proxies for FICO, same test we ran on `SELLER`.
- Quantifies the LP tilt: if 15-year loans default materially less, the objective's preference for 30-year paper is systematically steering toward risk, and that belongs in the report.

```
shape: (5, 6)
┌───────────┬─────────┬────────┬───────┬──────┬──────────┐
│ ORIG_TERM ┆ n       ┆ rate   ┆ fico  ┆ oltv ┆ rate_pct │
│ ---       ┆ ---     ┆ ---    ┆ ---   ┆ ---  ┆ ---      │
│ f64       ┆ u32     ┆ f64    ┆ f64   ┆ f64  ┆ f64      │
╞═══════════╪═════════╪════════╪═══════╪══════╪══════════╡
│ 120.0     ┆ 34215   ┆ 0.0121 ┆ 759.0 ┆ 52.1 ┆ 3.42     │
│ 180.0     ┆ 302536  ┆ 0.0192 ┆ 755.0 ┆ 64.6 ┆ 3.48     │
│ 240.0     ┆ 107811  ┆ 0.0213 ┆ 754.0 ┆ 68.4 ┆ 3.98     │
│ 300.0     ┆ 10886   ┆ 0.0284 ┆ 743.0 ┆ 71.1 ┆ 4.26     │
│ 360.0     ┆ 1577778 ┆ 0.0385 ┆ 748.0 ┆ 77.9 ┆ 4.29     │
└───────────┴─────────┴────────┴───────┴──────┴──────────┘
```

## Finding: 23% of the book is not a 30-year loan

`ORIG_TERM` has 235 distinct values.

| Term | n | Rate | FICO | OLTV |
|---|---|---|---|---|
| 120 | 34,215 | 1.21% | 759 | 52.1 |
| 180 | 302,536 | 1.92% | 755 | 64.6 |
| 240 | 107,811 | 2.13% | 754 | 68.4 |
| 300 | 10,886 | 2.84% | 743 | 71.1 |
| 360 | 1,577,778 | 3.85% | 748 | 77.9 |

The 3x spread is confounded. OLTV runs 52.1 to 77.9 across these rows, and a
26-point equity gap explains a 3x default difference on its own. FICO moves only
11 points. Term and equity travel together and this table cannot separate them.

**Effect:** keep `ORIG_TERM` as a feature; the model has both and can apportion.
Make no causal claim about term from this table.

**Limitation for the LP.** Same $200k at 7 years: a 30-year returns ~$52k
interest and ~$28k principal; a 15-year returns ~$37k interest and ~$81k
principal. The objective counts interest only, so it prefers 30-year paper. Part
of that is legitimate, since the 81bp term premium pays for real risk. What is
missing is that the 15-year frees ~$53k more capital by year 7, worth nothing in
a single-period model. The LP cannot see capital velocity.

## Logistic regression baseline

**What**
- Build train / calib / test matrices from the prepped frame.
- Fit LogReg with one-hot categoricals and scaled numerics.
- Report test AUC.

**Why LogReg first**
- Interpretable baseline. If the trees cannot beat it, the trees are misconfigured.
- It is the model that needs one-hot, so building it first validates the encoding for everything downstream.

**Encoding choices**
- `StandardScaler` on numerics: LogReg is scale-sensitive, and `ORIG_UPB` (~$200k) would otherwise swamp `DTI` (~35).
- `min_frequency=100` on the one-hot groups rare levels into `infrequent`. Handles the `PROPERTY_INSPECTION_WAIVER_INDICATOR` P and R levels (365 and 61 rows) without a special case.
- Flags pass through untouched. Already 0/1.

**Benchmarks**
- Synthetic PD scored 0.7178 on three hand-coefficiented features. LogReg on the full set should clear that.
- Mortgage PD models typically land 0.75 to 0.80.

```
matrices :   0.2s   train=(1227572, 26)  positives=41,810
fit      :   5.8s   width=130

AUC train: 0.7731
AUC test : 0.7705   (synthetic PD was 0.7178)
mean pred: 0.034125   actual: 0.034109
```

## XGBoost and LightGBM baselines

**What**
- Fit both with native categorical handling. No tuning.
- Report test AUC against the LogReg floor of 0.7705.

**Why native categoricals instead of one-hot**
- Both libraries split on categories directly. No 130-column expansion.
- `SELLER` at 37 levels and `STATE` at 54 are exactly where trees beat one-hot: they can group levels by response rather than testing each dummy separately.

**No early stopping, deliberately**
- Early stopping needs a watch set. The obvious candidate is `calib`, but that split is reserved for isotonic.
- Using `calib` to pick the stopping point means isotonic later fits on data the model was tuned against. Predictions there would be mildly optimistic and isotonic would learn a slightly wrong mapping. Subtle, and exactly the kind of thing that survives to the final report.
- Fixed rounds for baselines. When we tune, CV lives entirely inside `train`.

**No class weighting**
- `scale_pos_weight` and resampling distort predicted probabilities. Calibrated probabilities are the entire product of this stage.
- Still `OPEN` in ml_data.md. Decide after seeing these curves, not before.

**What to watch**
- Train-test AUC gap. Trees overfit where LogReg cannot, so a gap above ~0.02 means depth needs pulling in.

```
xgboost  :   6.2s
  AUC train 0.8165   test 0.7781
lightgbm :  11.1s
  AUC train 0.8377   test 0.7768

--- test AUC ---
  synthetic  0.7178
  logreg     0.7705
  xgboost    0.7781
  lightgbm   0.7768
```

## Finding: the signal in mortgage default is mostly linear

| Model | Test AUC | Train | Gap |
|---|---|---|---|
| Synthetic PD | 0.7178 | — | — |
| Logistic regression | 0.7705 | 0.7731 | 0.0026 |
| XGBoost | 0.7781 | 0.8165 | 0.0384 |
| LightGBM | 0.7768 | 0.8377 | 0.0609 |

Trees beat LogReg by 0.0076 and 0.0063. Real at 410k rows, small in practice.
FICO, LTV, and DTI carry the signal and carry it linearly. This is why the
industry ran on logistic scorecards for thirty years, and it belongs in the
report rather than buried.

LogReg's 0.0026 gap across 130 dummies means the `SELLER` and `STATE` dummies are
earning their place, not memorizing. Both trees exceed the 0.02 gap threshold.
LightGBM overfits harder and scores worse on test: `num_leaves=63` is too
permissive at a 3.4% base rate.

**No model selected yet.** AUC measures ranking. The LP does not rank, it does
arithmetic on the PD value: `(1-PD)·I - PD·L`. A model can rank perfectly and
still hand back PDs that are 40% too high. Calibration decides this.

## Calibration curves, raw predictions

**What**
- Bin test predictions, compare mean predicted PD to observed default rate per bin.
- Brier score and ECE for all three models.
- No isotonic yet. This measures the problem before the fix.

**Why this matters more than AUC here**
- AUC only asks whether risky loans rank above safe ones. The LP needs the numbers themselves to be right.
- `c_i = (1-PD) x income - PD x loss` is arithmetic on the PD value. A model that says 8% when the truth is 5% breaks the objective even with perfect ranking.
- The average-PD ceiling constraint is likewise a magnitude constraint. Miscalibrated PDs make it bind in the wrong place.

**Why quantile bins, not uniform**
- At a 3.4% base rate, uniform 0-to-1 bins put ~99% of loans in the first bin and measure nothing.
- Quantile bins put equal counts in each, so every bin is estimable.

**Metrics**
- ECE: average gap between predicted and observed across bins. Lower is better. This is the number to watch.
- Brier: mean squared error on probabilities. Rewards both ranking and calibration, so it is a useful tiebreak.

**Expect** LogReg near-calibrated (its intercept forces the mean to match) and the trees overconfident in the tail, per their train-test gaps.

```
catboost :  73.6s
  AUC train 0.7814   test 0.7750   gap 0.0064

  logreg 0.7705 | xgboost 0.7781 | lightgbm 0.7768
```

## Finding: CatBoost confirms the ceiling is the data

| Model | Test AUC | Train | Gap | Fit |
|---|---|---|---|---|
| Logistic regression | 0.7705 | 0.7731 | 0.0026 | 6s |
| XGBoost | 0.7781 | 0.8165 | 0.0384 | 6s |
| LightGBM | 0.7768 | 0.8377 | 0.0609 | 11s |
| CatBoost | 0.7750 | 0.7814 | 0.0064 | 75s |

CatBoost was run as a check, not a candidate. It is built for exactly what this
data has: high-cardinality categoricals (`SELLER` 37, `STATE` 54) and overfitting
resistance.

It did not beat XGBoost. Its ordered boosting worked as advertised, cutting the
gap from 0.038 and 0.061 down to 0.0064, and gained no AUC doing it. So the
overfitting was never the constraint. All three trees land at 0.775-0.778
regardless of algorithm, which makes "the signal is linear" a hard claim rather
than a suspicion that we tuned badly.

**Effect:** diagnostic only, not in the deliverable. Scope stays at three models.
The 0.0031 between XGBoost and CatBoost is inside noise at 13,982 positives.

## Calibration: does an 8% prediction actually default 8% of the time?

**The distinction that matters**

AUC asks one question: do risky loans rank above safe ones? That is all. A model
that predicts 8% for every loan that truly defaults at 4%, and 2% for every loan
that truly defaults at 1%, has **perfect AUC**. It ranks flawlessly. Every one of
its numbers is double the truth.

Calibration asks the other question: when the model says 8%, do 8 out of 100 of
those loans actually default?

**Why the LP forces this**

Most classification projects only need ranking. Ours does not. The objective is:

```
c_i = (1 - PD_i) x interest_income_7yr_i  -  PD_i x loss_if_default_i
```

That is arithmetic **on the PD value itself**, not on its rank. Feed it PDs that
are uniformly 2x too high and every expected return comes out wrong, the LP funds
the wrong loans, and AUC never notices. The average-PD ceiling constraint is a
magnitude constraint too: a ceiling of 3% means nothing if the PDs are inflated.

So the model with the best AUC is not automatically the model we ship. That is
why no model was selected after the AUC baselines.

**Reading a calibration table**

Sort predictions low to high, cut into 10 equal-count bins, and for each bin
compare the mean prediction to the observed default rate.

- `pred` = what the model claimed, averaged over the bin
- `obs` = what actually happened in that bin
- `gap` = `obs - pred`. Zero is perfect. Negative means the model **overpredicted**
  (claimed more risk than reality), positive means it **underpredicted**.
- `ratio` = `obs / pred`. Easier to read at low PDs. A 0.004 gap on a 0.008
  prediction looks tiny but is a 50% error. `ratio` shows it as 1.50.

Perfect calibration plots as the diagonal. Points below the line mean
overprediction; above means underprediction.

**Why quantile bins and not uniform 0-to-1 bins**
- At a 3.4% base rate, uniform bins put ~99% of loans in the first bin. Nine
  bins would sit empty and measure nothing.
- Equal-count bins mean every bin has ~41,000 loans and is estimable.

**Why two panels**
- Nine of ten bins live below 10% PD. That is where the LP's marginal funding
  decisions happen, and the full-range plot compresses them into the corner.
- The zoom is the panel that matters. The full range only shows the tail.

**The metrics**
- **ECE** (expected calibration error): the count-weighted average of `|obs - pred|`
  across bins. The single number to watch. Lower is better.
- **Brier**: mean squared error on the probabilities. Rewards ranking *and*
  calibration together, useful as a tiebreak.

**What to expect, and why**
- LogReg should look near-calibrated. Its intercept forces the mean prediction to
  match the base rate on the training distribution. That is a structural
  property, not a virtue.
- XGBoost and LightGBM should be visibly overconfident, pushed toward the
  extremes. Their train-test gaps were 0.038 and 0.061, and an overfit model is
  an overconfident model: it "knows" the training rows and pushes probabilities
  outward.
- CatBoost had a 0.0064 gap, so its raw calibration should be the cleanest of the
  trees.

**This is the before picture.** No isotonic yet. This cell measures the problem
so we can show what the fix bought. If the trees come back badly miscalibrated
here and clean after isotonic, that is the evidence that the calibration step
earns its place in the pipeline.

```
logreg     ECE 0.00103   Brier 0.031580   AUC 0.7705
shape: (10, 6)
┌─────┬───────┬────────┬────────┬─────────┬───────┐
│ bin ┆ n     ┆ pred   ┆ obs    ┆ gap     ┆ ratio │
│ --- ┆ ---   ┆ ---    ┆ ---    ┆ ---     ┆ ---   │
│ i64 ┆ i64   ┆ f64    ┆ f64    ┆ f64     ┆ f64   │
╞═════╪═══════╪════════╪════════╪═════════╪═══════╡
│ 0   ┆ 40993 ┆ 0.0032 ┆ 0.0026 ┆ -0.0006 ┆ 0.8   │
│ 1   ┆ 40992 ┆ 0.0063 ┆ 0.0057 ┆ -0.0007 ┆ 0.89  │
│ 2   ┆ 40993 ┆ 0.0095 ┆ 0.0097 ┆ 0.0002  ┆ 1.02  │
│ 3   ┆ 40992 ┆ 0.0133 ┆ 0.0137 ┆ 0.0004  ┆ 1.03  │
│ 4   ┆ 40993 ┆ 0.018  ┆ 0.0171 ┆ -0.0008 ┆ 0.95  │
│ 5   ┆ 40993 ┆ 0.0241 ┆ 0.0241 ┆ 0.0     ┆ 1.0   │
│ 6   ┆ 40992 ┆ 0.0324 ┆ 0.0338 ┆ 0.0014  ┆ 1.04  │
│ 7   ┆ 40992 ┆ 0.0446 ┆ 0.0462 ┆ 0.0016  ┆ 1.03  │
│ 8   ┆ 40993 ┆ 0.065  ┆ 0.0665 ┆ 0.0015  ┆ 1.02  │
│ 9   ┆ 40993 ┆ 0.1249 ┆ 0.1218 ┆ -0.0031 ┆ 0.98  │
└─────┴───────┴────────┴────────┴─────────┴───────┘

xgboost    ECE 0.00123   Brier 0.031481   AUC 0.7781
shape: (10, 6)
┌─────┬───────┬────────┬────────┬─────────┬───────┐
│ bin ┆ n     ┆ pred   ┆ obs    ┆ gap     ┆ ratio │
│ --- ┆ ---   ┆ ---    ┆ ---    ┆ ---     ┆ ---   │
│ i64 ┆ i64   ┆ f64    ┆ f64    ┆ f64     ┆ f64   │
╞═════╪═══════╪════════╪════════╪═════════╪═══════╡
│ 0   ┆ 40993 ┆ 0.0022 ┆ 0.0023 ┆ 0.0     ┆ 1.02  │
│ 1   ┆ 40992 ┆ 0.005  ┆ 0.0047 ┆ -0.0003 ┆ 0.93  │
│ 2   ┆ 40993 ┆ 0.0081 ┆ 0.0084 ┆ 0.0004  ┆ 1.04  │
│ 3   ┆ 40992 ┆ 0.0118 ┆ 0.0127 ┆ 0.0009  ┆ 1.08  │
│ 4   ┆ 40993 ┆ 0.0167 ┆ 0.0176 ┆ 0.0009  ┆ 1.06  │
│ 5   ┆ 40992 ┆ 0.0231 ┆ 0.0248 ┆ 0.0016  ┆ 1.07  │
│ 6   ┆ 40993 ┆ 0.032  ┆ 0.032  ┆ 0.0     ┆ 1.0   │
│ 7   ┆ 40991 ┆ 0.0449 ┆ 0.0463 ┆ 0.0014  ┆ 1.03  │
│ 8   ┆ 40994 ┆ 0.0667 ┆ 0.0678 ┆ 0.0012  ┆ 1.02  │
│ 9   ┆ 40993 ┆ 0.1301 ┆ 0.1245 ┆ -0.0056 ┆ 0.96  │
└─────┴───────┴────────┴────────┴─────────┴───────┘

lightgbm   ECE 0.00114   Brier 0.031502   AUC 0.7768
shape: (10, 6)
┌─────┬───────┬────────┬────────┬────────┬───────┐
│ bin ┆ n     ┆ pred   ┆ obs    ┆ gap    ┆ ratio │
│ --- ┆ ---   ┆ ---    ┆ ---    ┆ ---    ┆ ---   │
│ i64 ┆ i64   ┆ f64    ┆ f64    ┆ f64    ┆ f64   │
╞═════╪═══════╪════════╪════════╪════════╪═══════╡
│ 0   ┆ 40993 ┆ 0.0023 ┆ 0.0023 ┆ 0.0001 ┆ 1.03  │
│ 1   ┆ 40992 ┆ 0.005  ┆ 0.0051 ┆ 0.0    ┆ 1.01  │
│ 2   ┆ 40993 ┆ 0.008  ┆ 0.0082 ┆ 0.0001 ┆ 1.02  │
│ 3   ┆ 40992 ┆ 0.0118 ┆ 0.013  ┆ 0.0012 ┆ 1.1   │
│ 4   ┆ 40993 ┆ 0.0165 ┆ 0.0171 ┆ 0.0005 ┆ 1.03  │
│ 5   ┆ 40992 ┆ 0.0229 ┆ 0.0253 ┆ 0.0024 ┆ 1.11  │
│ 6   ┆ 40993 ┆ 0.0319 ┆ 0.032  ┆ 0.0001 ┆ 1.0   │
│ 7   ┆ 40992 ┆ 0.045  ┆ 0.046  ┆ 0.001  ┆ 1.02  │
│ 8   ┆ 40993 ┆ 0.0671 ┆ 0.0679 ┆ 0.0008 ┆ 1.01  │
│ 9   ┆ 40993 ┆ 0.1292 ┆ 0.1242 ┆ -0.005 ┆ 0.96  │
└─────┴───────┴────────┴────────┴────────┴───────┘

catboost   ECE 0.00086   Brier 0.031480   AUC 0.7750
shape: (10, 6)
┌─────┬───────┬────────┬────────┬─────────┬───────┐
│ bin ┆ n     ┆ pred   ┆ obs    ┆ gap     ┆ ratio │
│ --- ┆ ---   ┆ ---    ┆ ---    ┆ ---     ┆ ---   │
│ i64 ┆ i64   ┆ f64    ┆ f64    ┆ f64     ┆ f64   │
╞═════╪═══════╪════════╪════════╪════
... [truncated]
```

## Finding: all four models are already calibrated

| Model | ECE | Brier | AUC |
|---|---|---|---|
| CatBoost | 0.00086 | 0.031480 | 0.7750 |
| LogReg | 0.00103 | 0.031580 | 0.7705 |
| LightGBM | 0.00114 | 0.031502 | 0.7768 |
| XGBoost | 0.00123 | 0.031481 | 0.7781 |

ECE of 0.001 against a 3.4% base rate means the average bin is off by a tenth of
a percentage point.

This is expected. All four minimize log-loss, which is a proper scoring rule: it
is lowest exactly when the predicted probability equals the true one. Calibration
is what training was already asking for. Add 1.2M rows and no class weighting and
there is little left to fix.

**ECE has a floor.** At ~41k loans per bin, sampling noise is roughly ±0.0008, so
a perfect model would still score ~0.0006 here. CatBoost at 0.00086 is 1.4x the
floor, about as good as this test set can measure.

**The overfitting shows in bin 9**, the top decile at ~12% PD:

| Model | pred | obs | |
|---|---|---|---|
| XGBoost | 0.1301 | 0.1245 | over by 4.5% |
| LightGBM | 0.1292 | 0.1242 | over by 4.0% |
| CatBoost | 0.1228 | 0.1241 | under by 1.0% |

**This depends on the split.** Train and test were assigned at random, so both
come from the same 2017 pool and look alike (statistically: independent and
identically distributed, or IID). That is the easiest case for calibration to
carry over, and not what a deployed model faces. A lender trains on old vintages
and scores applicants in a different economy. Say this in the report rather than
claiming the models are calibrated in general.

**Effect.** Isotonic still runs: it is in the goal statement and costs nothing.
The likely finding is that it changes little, which is worth reporting. It could
also make calibration worse by fitting noise, so measure on test.

Selection stays open. CatBoost and XGBoost tie on Brier (1e-6 apart). CatBoost
wins ECE, XGBoost wins AUC by 0.0031.

## Calibration, magnified

**Why not just zoom**
- Bins are quantile-based, so they are log-spaced: eight of ten fall below 0.05. Linear cropping cannot separate them.

**Left panel: log-log**
- Even spacing across the full PD range. Equal visual weight to bin 0 and bin 9.

**Right panel: ratio**
- `obs / pred` against `pred`. Flat line at 1.0 is perfect.
- Above 1.0 = model underpredicted. Below = overpredicted.
- Shaded band is +/- 10%. Inside it, the error is smaller than the LP will notice.
- This is the panel that decides the model.

```
<Figure size 1300x550 with 2 Axes>
```

## Finding: plots confirm calibration; the ratio view misleads

All four models sit on the diagonal across three orders of magnitude. Calibration
confirmed by eye, not just by ECE.

**The ratio panel is the wrong lens.** The LP objective is
`c_i = (1-PD)·I - PD·L`. It is linear in PD, so an error of 0.005 costs the same
whether the PD is 0.01 or 0.12. Only the size of the error matters, not the
percentage.

| | ratio | actual error |
|---|---|---|
| CatBoost bin 0 | 0.75, looks bad | 0.0008 |
| XGBoost bin 9 | 0.96, looks fine | 0.0056 |

XGBoost is off by 7x more in the units the LP cares about. ECE already measures
error size, so it stays the metric. Use the ratio panel to see shape, not to pick
a model.

**The tails split.** The overfit models (XGBoost, LightGBM) get the safest loans
right and overshoot the riskiest. CatBoost does the opposite. Its regularization
helps where data is thin and hurts where predictions need to be extreme.

## Isotonic calibration

**What:** fit isotonic regression on the `calib` split, apply it to `test`,
compare ECE / Brier / AUC before and after.

**Why isotonic:** it learns any increasing mapping from predicted to true
probability without assuming a shape. Platt scaling forces a sigmoid; isotonic
does not. Because the mapping only ever increases, it cannot reorder loans, so
AUC should barely move.

**Why `calib` and not `train`:** on train it would learn to correct predictions
the models had memorized, and the mapping would be wrong for new loans. `calib`
is 409,353 loans with 14,094 positives, never seen during training.

**Success is not "ECE improves."** The models are already near the measurement
floor. Success is ECE not getting worse, plus a smaller error in bin 9.

**The check that matters:** isotonic can output exactly 0. A PD of 0 tells the LP
a loan is risk-free, and that loan wins the objective outright. Counted below.

```
calib preds :   1.5s

--- zero-PD check ---
  logreg    zeros:  1,235   min: 0.000000   max: 0.4444
  xgboost   zeros:    316   min: 0.000000   max: 0.2857
  lightgbm  zeros:    672   min: 0.000000   max: 0.3871
  catboost  zeros:  3,168   min: 0.000000   max: 0.7500

logreg +iso  ECE 0.00117   Brier 0.031577   AUC 0.7702
shape: (10, 6)
┌─────┬───────┬────────┬────────┬─────────┬───────┐
│ bin ┆ n     ┆ pred   ┆ obs    ┆ gap     ┆ ratio │
│ --- ┆ ---   ┆ ---    ┆ ---    ┆ ---     ┆ ---   │
│ i64 ┆ i64   ┆ f64    ┆ f64    ┆ f64     ┆ f64   │
╞═════╪═══════╪════════╪════════╪═════════╪═══════╡
│ 0   ┆ 37334 ┆ 0.0027 ┆ 0.0025 ┆ -0.0002 ┆ 0.91  │
│ 1   ┆ 33822 ┆ 0.0055 ┆ 0.0046 ┆ -0.0009 ┆ 0.83  │
│ 2   ┆ 50549 ┆ 0.008  ┆ 0.0093 ┆ 0.0013  ┆ 1.16  │
│ 3   ┆ 40946 ┆ 0.013  ┆ 0.0136 ┆ 0.0006  ┆ 1.05  │
│ 4   ┆ 34619 ┆ 0.0175 ┆ 0.0161 ┆ -0.0014 ┆ 0.92  │
│ 5   ┆ 40359 ┆ 0.0223 ┆ 0.0231 ┆ 0.0008  ┆ 1.04  │
│ 6   ┆ 44845 ┆ 0.0316 ┆ 0.0323 ┆ 0.0007  ┆ 1.02  │
│ 7   ┆ 35287 ┆ 0.0455 ┆ 0.0426 ┆ -0.0029 ┆ 0.94  │
│ 8   ┆ 44726 ┆ 0.0626 ┆ 0.0617 ┆ -0.0009 ┆ 0.99  │
│ 9   ┆ 47439 ┆ 0.1181 ┆ 0.1161 ┆ -0.002  ┆ 0.98  │
└─────┴───────┴────────┴────────┴─────────┴───────┘

xgboost +iso  ECE 0.00100   Brier 0.031479   AUC 0.7780
shape: (10, 6)
┌─────┬───────┬────────┬────────┬─────────┬───────┐
│ bin ┆ n     ┆ pred   ┆ obs    ┆ gap     ┆ ratio │
│ --- ┆ ---   ┆ ---    ┆ ---    ┆ ---     ┆ ---   │
│ i64 ┆ i64   ┆ f64    ┆ f64    ┆ f64     ┆ f64   │
╞═════╪═══════╪════════╪════════╪═════════╪═══════╡
│ 0   ┆ 32208 ┆ 0.0022 ┆ 0.002  ┆ -0.0002 ┆ 0.92  │
│ 1   ┆ 49502 ┆ 0.0049 ┆ 0.0044 ┆ -0.0004 ┆ 0.91  │
│ 2   ┆ 38992 ┆ 0.007  ┆ 0.0082 ┆ 0.0012  ┆ 1.18  │
│ 3   ┆ 40675 ┆ 0.0117 ┆ 0.0126 ┆ 0.0009  ┆ 1.07  │
│ 4   ┆ 39057 ┆ 0.0165 ┆ 0.017  ┆ 0.0005  ┆ 1.03  │
│ 5   ┆ 44574 ┆ 0.024  ┆ 0.0243 ┆ 0.0003  ┆ 1.01  │
│ 6   ┆ 33489 ┆ 0.031  ┆ 0.0303 ┆ -0.0007 ┆ 0.98  │
│ 7   ┆ 44624 ┆ 0.0439 ┆ 0.0439 ┆ -0.0    ┆ 1.0   │
│ 8   ┆ 44354 ┆ 0.0678 ┆ 0.0658 ┆ -0.0019 ┆ 0.97  │
│ 9   ┆ 42451 ┆ 0.1265 ┆ 0.123  ┆ -0.0035 ┆ 0.97  │
└─────┴───────┴────────┴────────┴─────────┴───────┘

lightgbm +iso  ECE 0.00096   Brier 0.031503   AUC 0.7766
shape: (10, 6)
┌─────┬───────┬────────┬────────┬─────────┬───────┐
│ bin ┆ n     ┆ pred   ┆ obs    ┆ gap     ┆ ratio │
│ --- ┆ ---   ┆ ---    ┆ ---    ┆ ---     ┆ ---   │
│ i64 ┆ i64   ┆ f64    ┆ f64    ┆ f64     ┆ f64   │
╞═════╪═══════╪════════╪════════╪═════════╪═══════╡
│ 0   ┆ 40912 ┆ 0.0025 ┆ 0.0023 ┆ -0.0002 ┆ 0.93  │
│ 1   ┆ 31615 ┆ 0.0047 ┆ 0.0048 ┆ 0.0002  ┆ 1.03  │
│ 2   ┆ 39314 ┆ 0.0068 ┆ 0.0068 ┆ -0.0001 ┆ 0.99  │
│ 3   ┆ 43162 ┆ 0.0109 ┆ 0.0122 ┆ 0.0013  ┆ 1.12  │
│ 4   ┆ 46353 ┆ 0.0163 ┆ 0.0165 ┆ 0.0003  ┆ 1.02  │
│ 5   ┆ 43194 ┆ 0.0235 ┆ 0.0246 ┆ 0.0012  ┆ 1.05  │
│ 6   ┆ 41001 ┆ 0.0329 ┆ 0.0316 ┆ -0.0013 ┆ 0.96  │
│ 7   ┆ 37595 ┆ 0.0458 ┆ 0.045  ┆ -0.0008 ┆ 0.98  │
│ 8   ┆ 39918 ┆ 0.0653 ┆ 0.064  ┆ -0.0013 ┆ 0.98  │
│ 9   ┆ 46862 ┆ 0.1218 ┆ 0.1189 ┆ -0.003  ┆ 0.98  │
└─────┴───────┴────────┴────────┴─────────┴───────┘

catboost +iso  ECE 
... [truncated]
```

## Finding: isotonic changes nothing and costs a little

| model | ECE raw | ECE iso | delta | AUC raw | AUC iso |
|---|---|---|---|---|---|
| logreg | 0.00103 | 0.00117 | +0.00014 | 0.7705 | 0.7702 |
| xgboost | 0.00123 | 0.00100 | -0.00023 | 0.7781 | 0.7780 |
| lightgbm | 0.00114 | 0.00096 | -0.00018 | 0.7768 | 0.7766 |
| catboost | 0.00086 | 0.00094 | +0.00008 | 0.7750 | 0.7747 |

Every delta is smaller than the ~0.0006 measurement floor. Two models improved,
two got worse. That pattern is noise, not signal. Brier is unchanged to the fifth
decimal.

**It costs AUC.** All four dropped. Isotonic maps distinct predictions to the same
value, which destroys ranking information. The bin counts show it: raw bins were
all ~40,993 by construction, but after isotonic LogReg's bin 1 holds 33,822 and
bin 2 holds 50,549. Those are ties.

**It introduces PD = 0.** Every model now has loans it calls risk-free:

| model | zeros | max |
|---|---|---|
| catboost | 3,168 | 0.75 |
| logreg | 1,235 | 0.4444 |
| lightgbm | 672 | 0.3871 |
| xgboost | 316 | 0.2857 |

A PD of 0 tells the LP the loan cannot default, so its expected return is the full
interest and it gets funded first. Nothing in the data supports that claim. It
happens because isotonic's bottom block covered a stretch of `calib` where no
loans defaulted, and it has no prior pulling it off zero.

**The tail rests on tiny samples.** Those max values are simple fractions: 0.75,
4/9, 2/7. Isotonic's top block is a handful of loans, and its estimate of the
riskiest PDs is fit on single-digit counts.

**Decision: ship raw predictions.** The models were already calibrated.
Isotonic's only measurable effects here are lost AUC and impossible PDs. This
does not mean isotonic is wrong in general. Under an IID split there is nothing
for it to correct. Under a temporal split across vintages there would be.

## Model selection: CatBoost

| | CatBoost | XGBoost |
|---|---|---|
| Test AUC | 0.7750 | 0.7781 |
| Brier | 0.031480 | 0.031481 |
| ECE | 0.00086 | 0.00123 |
| Train-test gap | 0.0064 | 0.0384 |

AUC and Brier are ties. The 0.0031 AUC difference is inside noise at 13,982
positives, and Brier separates them at the sixth decimal.

The train-test gap does not tie. CatBoost's is 6x smaller, meaning it is not
leaning on memorized training rows. That matters because our calibration result
already carries an IID caveat: it holds because train and test are the same
distribution. Shipping the model with the larger gap alongside that caveat is a
weak position.

**Decision:** CatBoost, raw predictions, no isotonic. Untuned. This notebook is
scaffolding to unblock the LP; track 1 delivers the tuned model in week 6.

## Naive baseline scorer

**What:** a rule-based risk score with no ML in it. Bucket the training loans by
FICO grade x Loan-To-Value (LTV) band, compute the plain historical default rate in each bucket,
then score test loans by looking up which bucket they fall in.

**Why it exists:** our claim is that calibrated probabilities plus optimization
beat a naive rule. If the naive rule ranked loans using CatBoost's PDs, both
strategies would share the same risk numbers and we would only be testing LP vs
greedy. This scorer owes nothing to the model, so the comparison is real.

**Why these bins:** `credit_grade` is already built from `CSCORE_B`. LTV cuts at
60/70/80/90/95 which mirror what an underwriter uses, and 80 is the mortgage insurance
boundary. 5 credit grades x 6 LTV bins = 30 buckets.

**Built on train only.** Same rule as the model. Using test to build the lookup
would leak the answers into the baseline and flatter it.

**Thin buckets fall back.** Fewer than 500 loans and the bucket rate is unstable,
so it falls back to the FICO grade's overall rate. Still rule-based, just
coarser.

**The check:** this should score meaningfully worse than CatBoost's 0.7750 AUC.
If it scores close, the model is not earning its place.

```
--- default rate % by credit grade (rows) x OLTV bin (cols), train only ---
shape: (5, 7)
┌──────────────┬───────────┬────────────┬────────────┬────────────┬────────────┬──────────┐
│ credit_grade ┆ OLTV <=60 ┆ OLTV 60-70 ┆ OLTV 70-80 ┆ OLTV 80-90 ┆ OLTV 90-95 ┆ OLTV >95 │
│ ---          ┆ ---       ┆ ---        ┆ ---        ┆ ---        ┆ ---        ┆ ---      │
│ str          ┆ f64       ┆ f64        ┆ f64        ┆ f64        ┆ f64        ┆ f64      │
╞══════════════╪═══════════╪════════════╪════════════╪════════════╪════════════╪══════════╡
│ Exceptional  ┆ 0.57      ┆ 0.86       ┆ 0.87       ┆ 1.08       ┆ 1.38       ┆ 2.74     │
│ Very Good    ┆ 1.26      ┆ 1.62       ┆ 1.81       ┆ 2.13       ┆ 2.78       ┆ 3.82     │
│ Good         ┆ 3.43      ┆ 4.53       ┆ 4.79       ┆ 5.36       ┆ 7.44       ┆ 8.25     │
│ Fair/Poor    ┆ 7.16      ┆ 8.94       ┆ 9.77       ┆ 12.07      ┆ 15.92      ┆ 15.41    │
│ Unknown      ┆ 2.95      ┆ 2.95       ┆ 2.95       ┆ 2.95       ┆ 2.95       ┆ 2.95     │
└──────────────┴───────────┴────────────┴────────────┴────────────┴────────────┴──────────┘

--- loan counts per bucket ---
shape: (5, 7)
┌──────────────┬───────────┬────────────┬────────────┬────────────┬────────────┬──────────┐
│ credit_grade ┆ OLTV <=60 ┆ OLTV 60-70 ┆ OLTV 70-80 ┆ OLTV 80-90 ┆ OLTV 90-95 ┆ OLTV >95 │
│ ---          ┆ ---       ┆ ---        ┆ ---        ┆ ---        ┆ ---        ┆ ---      │
│ str          ┆ u32       ┆ u32        ┆ u32        ┆ u32        ┆ u32        ┆ u32      │
╞══════════════╪═══════════╪════════════╪════════════╪════════════╪════════════╪══════════╡
│ Exceptional  ┆ 53714     ┆ 23362      ┆ 71352      ┆ 17486      ┆ 15456      ┆ 4015     │
│ Very Good    ┆ 106192    ┆ 66518      ┆ 226266     ┆ 70147      ┆ 80231      ┆ 30718    │
│ Good         ┆ 56759     ┆ 46126      ┆ 140786     ┆ 44435      ┆ 57533      ┆ 28006    │
│ Fair/Poor    ┆ 17927     ┆ 14883      ┆ 33068      ┆ 7712       ┆ 9857       ┆ 4074     │
│ Unknown      ┆ 140       ┆ 110        ┆ 430        ┆ 127        ┆ 110        ┆ 32       │
└──────────────┴───────────┴────────────┴────────────┴────────────┴────────────┴──────────┘

buckets: 30   fell back to grade rate: 6   book rate: 0.034059

--- scorer on test ---
  distinct scores : 25
  range           : 0.0057 to 0.1592
  mean            : 0.034054   actual: 0.034109

  AUC naive scorer : 0.7131
  AUC catboost     : 0.7750
```

## Finding: the naive scorer works, and it reframes our claim

Default rate % by credit grade x OLTV bin, train only:

| Grade | ≤60 | 60-70 | 70-80 | 80-90 | 90-95 | >95 |
|---|---|---|---|---|---|---|
| Exceptional | 0.57 | 0.86 | 0.87 | 1.08 | 1.38 | 2.74 |
| Very Good | 1.26 | 1.62 | 1.81 | 2.13 | 2.78 | 3.82 |
| Good | 3.43 | 4.53 | 4.79 | 5.36 | 7.44 | 8.25 |
| Fair/Poor | 7.16 | 8.94 | 9.77 | 12.07 | 15.92 | 15.41 |
| Unknown | 2.95 (fell back) |

Risk only rises as LTV goes up, and only rises as FICO goes down. Nothing forces
that ordering, so it is evidence the two features are real. Best bucket to worst
is 0.57% to 15.92%, a 28x spread.

FICO matters about twice as much as LTV. Across one row, worst LTV is 5x the best.
Down one column, worst FICO is 11x the best.

All six Unknown buckets are under 500 loans, so they fell back to the grade rate.
That gives 25 distinct scores, not 30.

**The comparison:**

| Scorer | AUC | Distinct scores |
|---|---|---|
| Naive lookup | 0.7131 | 25 |
| CatBoost | 0.7750 | ~410k |

CatBoost wins by 0.0619. But a coin flip scores 0.5, so the real gap is 0.2131 vs
0.2750: **two features in 25 buckets get 78% of what CatBoost gets from 26.**

**The naive scorer is calibrated.** Predicted 0.034054, actual 0.034109. Not luck.
It is a real default rate applied to loans from the same pool, so it cannot be off.

That breaks our goal statement. We claim we will show calibrated probabilities
beat a naive rule. Both are calibrated. The difference is **resolution**: the naive
scorer gives every loan in a bucket the same number and cannot rank them against
each other. CatBoost can.

Better claim, and more honest. The LP needs to tell loans apart, not just be right
on average. Goal statement and shared docs need updating.

## Save artifacts

**What:** write the LP contract file, the four fitted models, the naive lookup,
and a results JSON per model.

**Why now:** nothing is on disk. A kernel restart loses the session.

**What we are not saving:** the train and calib splits. `hash(LOAN_ID) % 100`
regenerates them in seconds from the typed file, so writing 2M rows to preserve a
one-line function is wasted disk and a stale-copy risk. Only the test split
matters, and it goes in the pool file with scores attached.

**The pool file carries all four models' PDs**, not just CatBoost. Four float
columns on 410k rows is free, and it lets the LP notebook test whether the
portfolio changes when the model swaps. That is a robustness result for the
report at zero cost.

**Pickle caveat:** joblib embeds library versions, so a teammate on a different
xgboost may not be able to load these. Acceptable for scaffolding: if a pickle
breaks, rerun the notebook. The feature list in each JSON is the real contract,
since CatBoost needs the exact column order and categorical dtypes.

```
saved scaffold_logreg_model.pkl + results.json
saved scaffold_xgboost_model.pkl + results.json
saved scaffold_lightgbm_model.pkl + results.json
saved scaffold_catboost_model.pkl + results.json
saved scaffold_naive_model.json + results.json

saved scaffold_pool.parquet   (409926, 16)
shape: (3, 16)
┌─────────────┬───────┬─────────────┬────────────┬──────────┬───────────┬───────────┬─────────────┬─────────────┬─────┬─────────────┬─────────────┬─────────────┬────────────┬─────────────┬───────────┐
│ LOAN_ID     ┆ STATE ┆ credit_grad ┆ ltv_bin    ┆ ORIG_UPB ┆ ORIG_TERM ┆ ORIG_RATE ┆ interest_in ┆ loss_if_def ┆ lgd ┆ score_naive ┆ default_fla ┆ pd_catboost ┆ pd_xgboost ┆ pd_lightgbm ┆ pd_logreg │
│ ---         ┆ ---   ┆ e           ┆ ---        ┆ ---      ┆ ---       ┆ ---       ┆ come_7yr    ┆ ault        ┆ --- ┆ ---         ┆ g           ┆ ---         ┆ ---        ┆ ---         ┆ ---       │
│ str         ┆ str   ┆ ---         ┆ str        ┆ f64      ┆ f64       ┆ f64       ┆ ---         ┆ ---         ┆ f64 ┆ f64         ┆ ---         ┆ f64         ┆ f32        ┆ f64         ┆ f64       │
│             ┆       ┆ str         ┆            ┆          ┆           ┆           ┆ f64         ┆ f64         ┆     ┆             ┆ i8          ┆             ┆            ┆             ┆           │
╞═════════════╪═══════╪═════════════╪════════════╪══════════╪═══════════╪═══════════╪═════════════╪═════════════╪═════╪═════════════╪═════════════╪═════════════╪════════════╪═════════════╪═══════════╡
│ 12313787084 ┆ TX    ┆ Good        ┆ OLTV >95   ┆ 180000.0 ┆ 360.0     ┆ 4.375     ┆ 51712.29474 ┆ 54000.0     ┆ 0.3 ┆ 0.082518    ┆ 1           ┆ 0.149415    ┆ 0.159556   ┆ 0.160999    ┆ 0.145756  │
│ 7           ┆       ┆             ┆            ┆          ┆           ┆           ┆ 6           ┆             ┆     ┆             ┆             ┆             ┆            ┆             ┆           │
│ 10215712740 ┆ CA    ┆ Very Good   ┆ OLTV <=60  ┆ 203000.0 ┆ 360.0     ┆ 3.5       ┆ 46211.71616 ┆ 60900.0     ┆ 0.3 ┆ 0.012581    ┆ 0           ┆ 0.006058    ┆ 0.005009   ┆ 0.004935    ┆ 0.004361  │
│ 7           ┆       ┆             ┆            ┆          ┆           ┆           ┆             ┆             ┆     ┆             ┆             ┆             ┆            ┆             ┆           │
│ 13844415210 ┆ CA    ┆ Good        ┆ OLTV 70-80 ┆ 520000.0 ┆ 360.0     ┆ 4.375     ┆ 149391.0737 ┆ 156000.0    ┆ 0.3 ┆ 0.047938    ┆ 0           ┆ 0.010089    ┆ 0.00499    ┆ 0.005275    ┆ 0.031284  │
│ 4           ┆       ┆             ┆            ┆          ┆           ┆           ┆ 11          ┆             ┆     ┆             ┆             ┆             ┆            ┆             ┆           │
└─────────────┴───────┴─────────────┴────────────┴──────────┴───────────┴───────────┴─────────────┴─────────────┴─────┴─────────────┴─────────────┴─────────────┴────────────┴─────────────┴───────────┘

--- sanity ---
  rows            : 409,926   (expect 409,926)
  nulls           : 0
  m
... [truncated]
```

```
shape: (1, 3)
┌──────────┬─────────────┬─────────────────┐
│ max_pd   ┆ above_40pct ┆ negative_return │
│ ---      ┆ ---         ┆ ---             │
│ f64      ┆ u32         ┆ u32             │
╞══════════╪═════════════╪═════════════════╡
│ 0.559477 ┆ 31          ┆ 2               │
└──────────┴─────────────┴─────────────────┘
```

## Finding: nearly every loan is profitable, so the constraints carry the LP

Max PD is 0.559. Break-even PD is `I / (L + I)`, roughly 47% for a 30-year and
40% for a 15-year. Only 31 loans clear 40% PD, and only **2 have negative
expected return**.

**The objective almost never says "don't fund this."** With 409,924 of 409,926
loans profitable, a budget-only LP would just buy the highest return per dollar
until the money ran out.

That matters because a budget-only fractional LP is a fractional knapsack, and
fractional knapsack has a provably optimal greedy solution: sort by
`c_i / ORIG_UPB_i`, fill until broke. Gurobi and a five-line sort would return the
identical portfolio.

**So the LP earns its keep entirely through the average-PD ceiling and the state
caps.** Those break the greedy structure and no sort can reproduce them. Worth
knowing before we design stage 3 rather than after.

**It also sharpens the naive baseline comparison.** Our naive rule funds
lowest-risk-first below a 3.4% cutoff. But low PD comes with low rates, since
better credit gets better pricing. So the naive rule systematically funds the
lowest-yielding loans and leaves money on the table, while the LP will fund
riskier, higher-yielding paper that is still profitable.

That is a third difference between the two strategies, stacked on top of
resolution. The naive rule ignores return entirely. Which one drives the win is
exactly what the 2x2 attribution would answer, if we want it.

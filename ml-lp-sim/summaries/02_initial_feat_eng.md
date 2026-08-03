# 02_initial_feat_eng

```
Rows: 2,046,851
Features: 115
```

```
Timing fields present: ['LOAN_AGE', 'ZB_DTE', 'ORIG_DATE', 'REM_MONTHS', 'MATR_DT']
LOAN_AGE          2,046,851 populated (100.0%)
ZB_DTE                    0 populated (0.0%)
ORIG_DATE         2,046,851 populated (100.0%)
REM_MONTHS        2,046,851 populated (100.0%)
MATR_DT           2,046,851 populated (100.0%)
```

## Interest Income Per Loan (Amortized, 7-Year Horizon)

Estimates the interest income each loan generates, to feed the expected-return
calculation in the LP stage.

Assumptions and rationale:
- **Amortized interest.** We compute the fixed monthly payment from the loan's
  rate, original balance, and full 360-month term, then sum the interest portion
  of the payments. Mortgage interest is front-loaded, so amortization captures
  the real income shape better than a flat approximation.
- **7-year effective horizon (84 payments).** We sum interest only through month
  84, not the full 30 years. Most 30-year mortgages terminate early through sale
  or refinance, so ~7 years reflects realized loan life. This also serves as a
  proxy for prepayment, which we otherwise ignore.
- **Payment set on full term.** The monthly payment uses the true 360-month
  schedule, since that is the borrower's actual contractual payment. We simply
  truncate the interest sum at year 7.
- **No discounting.** Interest is summed in nominal dollars, not present value.
  A simplification for this build; discounting is noted as possible future work.
- **Gross interest.** Servicing and

### Vectorized Cumulative Interest (Closed-Form)

Computes interest income over the 84-month horizon in closed form, no per-loan
loop. Logic: total paid over 84 months is (monthly payment x 84). The principal
retired over those months has a closed-form expression, so interest is the
difference between total paid and principal retired.

```
shape: (9, 5)
┌────────────┬───────────────┬────────────┬─────────────────┬─────────────────────┐
│ statistic  ┆ ORIG_UPB      ┆ ORIG_RATE  ┆ monthly_payment ┆ interest_income_7yr │
│ ---        ┆ ---           ┆ ---        ┆ ---             ┆ ---                 │
│ str        ┆ f64           ┆ f64        ┆ f64             ┆ f64                 │
╞════════════╪═══════════════╪════════════╪═════════════════╪═════════════════════╡
│ count      ┆ 2.046851e6    ┆ 2.046851e6 ┆ 2.046851e6      ┆ 2.046851e6          │
│ null_count ┆ 0.0           ┆ 0.0        ┆ 0.0             ┆ 0.0                 │
│ mean       ┆ 228839.312192 ┆ 4.140495   ┆ 1111.131769     ┆ 61984.344905        │
│ std        ┆ 119551.768064 ┆ 0.494707   ┆ 586.493053      ┆ 33637.694073        │
│ min        ┆ 5000.0        ┆ 1.79       ┆ 23.15578        ┆ 1222.987564         │
│ 25%        ┆ 137000.0      ┆ 3.875      ┆ 664.118853      ┆ 36689.626906        │
│ 50%        ┆ 206000.0      ┆ 4.125      ┆ 1001.562886     ┆ 55653.497672        │
│ 75%        ┆ 300000.0      ┆ 4.5        ┆ 1456.80493      ┆ 80934.325175        │
│ max        ┆ 1.223e6       ┆ 6.125      ┆ 7040.277822     ┆ 457173.492356       │
└────────────┴───────────────┴────────────┴─────────────────┴─────────────────────┘
```

## LGD Flat-Value Column

Attaches a Loss Given Default (LGD) value to each loan for the expected-loss
calculation in the LP and simulation stages.

Assumptions and rationale:
- **Flat value, not computed.** The Qi-Yang formula could not be applied here,
  since all recovery fields (net sales proceeds, foreclosure costs, etc.) are
  null across the full book. So we assign a flat LGD from the literature.
- **30% baseline.** Sirignano et al. (2016) use 30% for a normal economy and
  50% for a downturn. Our 2017 vintage sits in a stable housing period, so 30%
  is the baseline. The 50% value is reserved as a downturn stress scenario for
  the simulation stage.
- **Single tunable parameter.** LGD is set once, at the top, so it can be
  changed in one place and the column rebuilt.

```
LGD applied: 30%
shape: (3, 1)
┌─────┐
│ lgd │
│ --- │
│ f64 │
╞═════╡
│ 0.3 │
│ 0.3 │
│ 0.3 │
└─────┘
```

## Credit Grade Buckets

Groups loans into standard FICO credit bands from CSCORE_B, for use in EDA and
as a potential diversification dimension in the LP stage.

Definitions and rationale:
- **Standard FICO bands** are used for defensibility:
  - Exceptional: 800+
  - Very Good: 740 to 799
  - Good: 670 to 739
  - Fair/Poor (combined): below 670
- **Poor and Fair are combined.** The Poor band (below 580) holds only ~1,574
  loans and behaves erratically due to its small size, so merging it with Fair
  avoids noise while keeping the low-credit segment represented.
- **Source column:** CSCORE_B, the Borrower Credit Score at Origination, which
  the Fannie Mae glossary defines as the Classic FICO score.

```
shape: (5, 2)
┌──────────────┬────────┐
│ credit_grade ┆ count  │
│ ---          ┆ ---    │
│ str          ┆ u32    │
╞══════════════╪════════╡
│ Very Good    ┆ 967786 │
│ Good         ┆ 623257 │
│ Exceptional  ┆ 308739 │
│ Fair/Poor    ┆ 145496 │
│ Unknown      ┆ 1573   │
└──────────────┴────────┘
```

## Loss If Default (Dollar Loss Per Loan)

Computes the dollar loss a loan would incur if it defaults, for the
expected-return calculation in the LP stage.

Logic and scope:
- **loss_if_default = LGD x ORIG_UPB.** The fraction lost (LGD) times the loan
  balance gives the dollar loss on default.
- **PD not applied here.** Expected loss is PD x LGD x loan amount. PD comes
  from the ML stage, so we build the LGD x amount portion now and apply PD
  during post-ML assembly.
- Uses the flat LGD baseline set earlier (LGD_BASELINE).

```
shape: (9, 4)
┌────────────┬───────────────┬────────────┬─────────────────┐
│ statistic  ┆ ORIG_UPB      ┆ lgd        ┆ loss_if_default │
│ ---        ┆ ---           ┆ ---        ┆ ---             │
│ str        ┆ f64           ┆ f64        ┆ f64             │
╞════════════╪═══════════════╪════════════╪═════════════════╡
│ count      ┆ 2.046851e6    ┆ 2.046851e6 ┆ 2.046851e6      │
│ null_count ┆ 0.0           ┆ 0.0        ┆ 0.0             │
│ mean       ┆ 228839.312192 ┆ 0.3        ┆ 68651.793658    │
│ std        ┆ 119551.768064 ┆ 2.4832e-18 ┆ 35865.530419    │
│ min        ┆ 5000.0        ┆ 0.3        ┆ 1500.0          │
│ 25%        ┆ 137000.0      ┆ 0.3        ┆ 41100.0         │
│ 50%        ┆ 206000.0      ┆ 0.3        ┆ 61800.0         │
│ 75%        ┆ 300000.0      ┆ 0.3        ┆ 90000.0         │
│ max        ┆ 1.223e6       ┆ 0.3        ┆ 366900.0        │
└────────────┴───────────────┴────────────┴─────────────────┘
```

## Socio-Economic Constraint Indicators

Converts the three socio-economic flags into 0/1 integer columns for direct use
in Gurobi constraint sums. Kept as separate columns to preserve the distinction
between programs, since first-time buyer, HomeReady, and HFA Preferred each
behave differently.

- is_first_time: 1 if FIRST_FLAG is Y, else 0
- is_homeready: 1 if HOMEREADY_PROGRAM_INDICATOR is H, else 0
- is_hfa: 1 if HOMEREADY_PROGRAM_INDICATOR is F, else 0

State and credit grade are left as labels, to be grouped directly in the LP
stage rather than one-hot encoded here.

```
shape: (1, 3)
┌──────────────────┬─────────────────┬───────────┐
│ first_time_count ┆ homeready_count ┆ hfa_count │
│ ---              ┆ ---             ┆ ---       │
│ i64              ┆ i64             ┆ i64       │
╞══════════════════╪═════════════════╪═══════════╡
│ 488486           ┆ 103860          ┆ 52205     │
└──────────────────┴─────────────────┴───────────┘
```

```
Rows: 2,046,851
Features: 127

New feature columns present:
['interest_income_7yr', 'lgd', 'loss_if_default', 'credit_grade', 'is_first_time', 'is_homeready', 'is_hfa']
```

```
Rows: 2,046,851
Features: 123
```

## Save the Engineered Feature Set

Saves the finished dataset to its own file, so the original reduction file stays untouched.

Where the columns come from:
- Input: fannie_2017_loan_level.parquet, 117 columns (113 raw Fannie fields plus max_dlq_ever, zero_bal_code, default_flag, orig_quarter added during reduction).
- Added 8 columns here: monthly_payment, interest_income_7yr, lgd, loss_if_default, credit_grade, is_first_time, is_homeready, is_hfa.
- Dropped 4 scratch columns from the interest math: monthly_rate, balance_after_horizon, principal_retired, total_paid_horizon.
- Output: 123 columns.

Features we built and the assumptions behind them:
- interest_income_7yr: amortized interest over a 7-year (84-month) window. The monthly payment is set on the full 360-month term, but we only sum interest through month 84. This reflects that most 30-year mortgages end early through a sale or refinance, and stands in for prepayment. No discounting, gross interest only.
- lgd: flat 30 percent (Sirignano et al. 2016). The recovery fields are empty across the whole book, so the Qi-Yang formula cannot be used. Set as one tunable value (LGD_BASELINE); 50 percent is held back for a downturn stress test.
- loss_if_default: lgd times ORIG_UPB, the dollar loss if a loan defaults. PD gets applied later to turn this into expected loss.
- credit_grade: standard FICO bands (Exceptional, Very Good, Good, Fair/Poor), with Poor and Fair combined and a separate Unknown bucket for missing scores.
- is_first_time, is_homeready, is_hfa: 0/1 flags for the socio-economic constraints, kept separate so each program stays distinct.

```
Saved 2,046,851 rows x 123 columns to ../data/processed/fannie_2017_features_added.parquet
```

# 02_initial_feat_eng

# Feature Engineering: Building the LP Inputs

Stage 2 of the pipeline. The reduction step gave us one row per loan with the raw
Fannie fields. This notebook adds the columns the optimizer needs but the data does
not carry.

**What gets built here**

- **interest_income_7yr** and **monthly_payment**: what each loan earns over a
  7-year horizon, amortized on the loan's own term.
- **lgd** and **loss_if_default**: the dollar loss if a loan goes bad, using a flat
  30% loss rate from the literature.
- **credit_grade**: standard FICO bands, for grouping in EDA and the LP.
- **is_first_time, is_homeready, is_hfa**: 0/1 flags for the equity constraints.

**Scope**

Origination-time economics only. No default probabilities, no loan selection. PD
comes from the ML notebook and gets combined with these columns downstream.

**Output**

`fannie_2017_features_added.parquet`, 2,046,851 rows by 123 columns. This is the
file both the ML and EDA tracks read from.

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

### Cumulative Interest Over the Horizon (Closed-Form)

Computes the interest each loan earns over the first seven years, with no
per-loan loop.

The logic: interest is what you pay minus what you pay down. Total paid is the
monthly payment times the number of months. Principal retired is the original
balance minus whatever balance is left. Both have closed-form expressions, so
the whole book computes in a few vectorized passes.

Two details matter here:

- **Each loan uses its own term.** The monthly payment depends on how long the
  loan runs, so a 15-year loan pays more per month than a 30-year loan of the
  same size. About 23% of the book is not a 30-year loan, so using a fixed
  360-month schedule would overstate their interest by roughly 15% on average,
  and by 35% for 10-year loans.

- **Short loans stop earning at payoff.** The window is the smaller of 84 months
  and the loan's own term. Without this, a 36-month loan would keep accruing
  interest for four years after it was paid off.

This cell also recomputes `monthly_payment`, so the payment and the interest are
built from the same term assumption rather than drifting apart.

### Sanity Check the Interest Column

Three things that should never happen, plus a look at the results by term.

- **Negative interest or balance**: a sign the payment was built on the wrong term.
- **Principal retired above the original balance**: a sign the horizon ran past payoff.
- **Averages by term**: interest should rise with term, since longer loans pay down slower.

All three counts should be zero.

```
negative interest: 0
negative balance:  0
over-retired:      0
shape: (235, 4)
┌───────────┬─────────┬─────────────┬──────────────────┐
│ ORIG_TERM ┆ n       ┆ avg_payment ┆ avg_interest_7yr │
│ ---       ┆ ---     ┆ ---         ┆ ---              │
│ f64       ┆ u32     ┆ f64         ┆ f64              │
╞═══════════╪═════════╪═════════════╪══════════════════╡
│ 36.0      ┆ 1       ┆ 1778.0      ┆ 4012.0           │
│ 48.0      ┆ 1       ┆ 823.0       ┆ 2507.0           │
│ 60.0      ┆ 6       ┆ 842.0       ┆ 4204.0           │
│ 72.0      ┆ 1       ┆ 380.0       ┆ 2349.0           │
│ 84.0      ┆ 28      ┆ 1206.0      ┆ 11550.0          │
│ …         ┆ …       ┆ …           ┆ …                │
│ 356.0     ┆ 30      ┆ 1354.0      ┆ 73035.0          │
│ 357.0     ┆ 18      ┆ 1307.0      ┆ 73083.0          │
│ 358.0     ┆ 30      ┆ 1235.0      ┆ 68183.0          │
│ 359.0     ┆ 31      ┆ 1098.0      ┆ 60619.0          │
│ 360.0     ┆ 1577778 ┆ 1183.0      ┆ 67142.0          │
└───────────┴─────────┴─────────────┴──────────────────┘
```

### Book-Wide Interest Totals

Sums the corrected interest across all loans.

- The mean is the number to compare against the old $61,984 per loan.
- The gap between them is how much the LP objective shrinks once the term fix is in.

```
shape: (1, 2)
┌───────────┬──────────────┐
│ total     ┆ mean         │
│ ---       ┆ ---          │
│ f64       ┆ f64          │
╞═══════════╪══════════════╡
│ 1.2451e11 ┆ 60829.090575 │
└───────────┴──────────────┘
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
- **Poor and Fair are combined.** Only one loan in the entire book scores below
  580, which is what Fannie's conforming standards would predict. A separate Poor
  band would be a single borrower, so it merges into Fair.
- **Loans with no score get their own bucket.** 1,573 loans have a null CSCORE_B.
  They are labeled Unknown rather than swept into the lowest band, since a missing
  score is not the same as a bad one. They default at 2.8%, better than the Good
  band.
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
Features: 131

New feature columns present:
['interest_income_7yr', 'lgd', 'loss_if_default', 'credit_grade', 'is_first_time', 'is_homeready', 'is_hfa']
```

```
Rows: 2,046,851
Features: 127
```

## Save the Engineered Feature Set

Saves the finished dataset to its own file, so the original reduction file stays untouched.

Where the columns come from:
- Input: fannie_2017_loan_level.parquet, 117 columns (113 raw Fannie fields plus max_dlq_ever, zero_bal_code, default_flag, orig_quarter added during reduction).
- Added 8 columns here: monthly_payment, interest_income_7yr, lgd, loss_if_default, credit_grade, is_first_time, is_homeready, is_hfa.
- Dropped 8 scratch columns from the interest math: monthly_rate, balance_after_horizon, principal_retired, total_paid_horizon, _term, _eff_horizon, _growth_full, _growth_horizon.
- Output: 123 columns.

Features we built and the assumptions behind them:
- interest_income_7yr: amortized interest over a 7-year (84-month) window, or the loan's full term if shorter. The monthly payment is set on each loan's own term, since a 15-year loan pays more per month than a 30-year loan of the same size. The 7-year window reflects that most mortgages end early through a sale or refinance, and stands in for prepayment. That assumption fits 30-year loans best, and 23 percent of the book is shorter. No discounting, gross interest only.
- lgd: flat 30 percent (Sirignano et al. 2016). The recovery fields are empty across the whole book, so the Qi-Yang formula cannot be used. Set as one tunable value (LGD_BASELINE); 50 percent is held back for a downturn stress test.
- loss_if_default: lgd times ORIG_UPB, the dollar loss if a loan defaults. PD gets applied later to turn this into expected loss.
- credit_grade: standard FICO bands (Exceptional, Very Good, Good, Fair/Poor), with Poor and Fair combined since only one loan scores below 580, and a separate Unknown bucket for the 1,573 loans with no score.
- is_first_time, is_homeready, is_hfa: 0/1 flags for the socio-economic constraints, kept separate so each program stays distinct.

```
Saved 2,046,851 rows x 127 columns to ../data/processed/fannie_2017_features_added.parquet
```

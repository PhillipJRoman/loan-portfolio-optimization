# 01_data_initial_check

# Dataset Research: Foundations for ML, LP Constraints, and Simulation

This notebook explores the reduced Fannie Mae 2017 loan-level dataset to inform
the three modeling stages ahead. The goal is to understand the data well enough
to make grounded decisions in each stage:

- **Machine Learning:** target balance, feature distributions, and the risk
  gradient that a default model will need to capture.
- **Linear Programming constraints:** loan amount ranges to size the budget,
  and state and zip concentration to set diversification caps and the
  average-PD ceiling.
- **Simulation:** baseline default rates and risk structure that will feed the
  Monte Carlo comparison later.

All figures here use the historical default_flag as a stand-in for predicted
probability of default until the ML stage produces calibrated model output.

## Load Dataset and Check Size, Schema, and Target Balance

Loads the reduced loan-level file and confirms the basics before analysis:
row count, feature count, column dtypes, and the class balance of the target.
The default rate at the end gives a quick read on how imbalanced the problem is.

```
Rows: 2,046,851
Features: 115
Schema({'LOAN_ID': String, 'POOL_ID': String, 'ACT_PERIOD': String, 'CHANNEL': String, 'SELLER': String, 'SERVICER': String, 'MASTER_SERVICER': String, 'ORIG_RATE': String, 'CURR_RATE': String, 'ORIG_UPB': String, 'ISSUANCE_UPB': String, 'CURRENT_UPB': String, 'ORIG_TERM': String, 'ORIG_DATE': String, 'FIRST_PAY': String, 'LOAN_AGE': String, 'REM_MONTHS': String, 'ADJ_REM_MONTHS': String, 'MATR_DT': String, 'OLTV': String, 'OCLTV': String, 'NUM_BO': String, 'DTI': String, 'CSCORE_B': String, 'CSCORE_C': String, 'FIRST_FLAG': String, 'PURPOSE': String, 'PROP': String, 'NO_UNITS': String, 'OCC_STAT': String, 'STATE': String, 'MSA': String, 'ZIP': String, 'MI_PCT': String, 'PRODUCT': String, 'PPMT_FLG': String, 'IO': String, 'FIRST_PAY_IO': String, 'MNTHS_TO_AMTZ_IO': String, 'PMT_HISTORY': String, 'MOD_FLAG': String, 'MI_CANCEL_FLAG': String, 'ZB_DTE': String, 'LAST_UPB': String, 'RPRCH_DTE': String, 'CURR_SCHD_PRNCPL': String, 'TOT_SCHD_PRNCPL': String, 'UNSCHD_PRNCPL_CURR': String, 'LAST_PAID_INSTALLMENT_DATE': String, 'FORECLOSURE_DATE': String, 'DISPOSITION_DATE': String, 'FORECLOSURE_COSTS': String, 'PROPERTY_PRESERVATION_AND_REPAIR_COSTS': String, 'ASSET_RECOVERY_COSTS': String, 'MISCELLANEOUS_HOLDING_EXPENSES_AND_CREDITS': String, 'ASSOCIATED_TAXES_FOR_HOLDING_PROPERTY': String, 'NET_SALES_PROCEEDS': String, 'CREDIT_ENHANCEMENT_PROCEEDS': String, 'REPURCHASES_MAKE_WHOLE_PROCEEDS': String, 'OTHER_FORECLOSURE_PROCEEDS': String, 'NON_INTEREST_BEARING_UPB': String, 'PRINCIPAL_FORGIVENESS_AMOUNT': String, 'ORIGINAL_LIST_START_DATE': String, 'ORIGINAL_LIST_PRICE': String, 'CURRENT_LIST_START_DATE': String, 'CURRENT_LIST_PRICE': String, 'ISSUE_SCOREB': String, 'ISSUE_SCOREC': String, 'CURR_SCOREB': String, 'CURR_SCOREC': String, 'MI_TYPE': String, 'SERV_IND': String, 'CURRENT_PERIOD_MODIFICATION_LOSS_AMOUNT': String, 'CUMULATIVE_MODIFICATION_LOSS_AMOUNT': String, 'CURRENT_PERIOD_CREDIT_EVENT_NET_GAIN_OR_LOSS': String, 'CUMULATIVE_CREDIT_EVENT_NET_GAIN_OR_LOSS': String, 'HOMEREADY_PROGRAM_INDICATOR': String, 'FORECLOSURE_PRINCIPAL_WRITE_OFF_AMOUNT': String, 'RELOCATION_MORTGAGE_INDICATOR': String, 'ZERO_BALANCE_CODE_CHANGE_DATE': String, 'LOAN_HOLDBACK_INDICATOR': String, 'LOAN_HOLDBACK_EFFECTIVE_DATE': String, 'DELINQUENT_ACCRUED_INTEREST': String, 'PROPERTY_INSPECTION_WAIVER_INDICATOR': String, 'HIGH_BALANCE_LOAN_INDICATOR': String, 'ARM_5_YR_INDICATOR': String, 'ARM_PRODUCT_TYPE': String, 'MONTHS_UNTIL_FIRST_PAYMENT_RESET': String, 'MONTHS_BETWEEN_SUBSEQUENT_PAYMENT_RESET': String, 'INTEREST_RATE_CHANGE_DATE': String, 'PAYMENT_CHANGE_DATE': String, 'ARM_INDEX': String, 'ARM_CAP_STRUCTURE': String, 'INITIAL_INTEREST_RATE_CAP': String, 'PERIODIC_INTEREST_RATE_CAP': String, 'LIFETIME_INTEREST_RATE_CAP': String, 'MARGIN': String, 'BALLOON_INDICATOR': String, 'PLAN_NUMBER': String, 'FORBEARANCE_INDICATOR': String, 'HIGH_LOAN_TO_VALUE_HLTV_REFINANCE_OPTION_INDICATOR': String, 'DEAL_NAME': String, 'RE_PROCS_FLAG': String, '
... [truncated]
```

## Summary Statistics Across All Columns

A quick one-line overview of the full dataset. Gives count, null count, mean,
standard deviation, min, max, and quartiles for every column at once. Useful
for spotting ranges, missing data, and anything that looks off before deeper
analysis.

```
shape: (9, 116)
┌────────────┬───────────┬─────────┬───────────┬───┬───────────┬───────────┬───────────┬───────────┐
│ statistic  ┆ LOAN_ID   ┆ POOL_ID ┆ ACT_PERIO ┆ … ┆ max_dlq_e ┆ zero_bal_ ┆ default_f ┆ orig_quar │
│ ---        ┆ ---       ┆ ---     ┆ D         ┆   ┆ ver       ┆ code      ┆ lag       ┆ ter       │
│ str        ┆ str       ┆ str     ┆ ---       ┆   ┆ ---       ┆ ---       ┆ ---       ┆ ---       │
│            ┆           ┆         ┆ str       ┆   ┆ f64       ┆ str       ┆ f64       ┆ str       │
╞════════════╪═══════════╪═════════╪═══════════╪═══╪═══════════╪═══════════╪═══════════╪═══════════╡
│ count      ┆ 2046851   ┆ 0       ┆ 2046851   ┆ … ┆ 2.046851e ┆ 1528334   ┆ 2.046851e ┆ 2046851   │
│            ┆           ┆         ┆           ┆   ┆ 6         ┆           ┆ 6         ┆           │
│ null_count ┆ 0         ┆ 2046851 ┆ 0         ┆ … ┆ 0.0       ┆ 518517    ┆ 0.0       ┆ 0         │
│ mean       ┆ null      ┆ null    ┆ null      ┆ … ┆ 0.635931  ┆ null      ┆ 0.034143  ┆ null      │
│ std        ┆ null      ┆ null    ┆ null      ┆ … ┆ 2.760508  ┆ null      ┆ 0.181597  ┆ null      │
│ min        ┆ 100002130 ┆ null    ┆ 012017    ┆ … ┆ 0.0       ┆ 01        ┆ 0.0       ┆ 2017Q1    │
│            ┆ 634       ┆         ┆           ┆   ┆           ┆           ┆           ┆           │
│ 25%        ┆ null      ┆ null    ┆ null      ┆ … ┆ 0.0       ┆ null      ┆ 0.0       ┆ null      │
│ 50%        ┆ null      ┆ null    ┆ null      ┆ … ┆ 0.0       ┆ null      ┆ 0.0       ┆ null      │
│ 75%        ┆ null      ┆ null    ┆ null      ┆ … ┆ 0.0       ┆ null      ┆ 0.0       ┆ null      │
│ max        ┆ 999999115 ┆ null    ┆ 122017    ┆ … ┆ 96.0      ┆ 16        ┆ 1.0       ┆ 2017Q4    │
│            ┆ 492       ┆         ┆           ┆   ┆           ┆           ┆           ┆           │
└────────────┴───────────┴─────────┴───────────┴───┴───────────┴───────────┴───────────┴───────────┘
```

## Quick Data Inspection Commands

A reference set of Polars commands for getting oriented in the dataset:
schema and dtypes, a transposed preview of values, null counts per column,
a row preview, and a frequency table for a single column. Useful as a first
pass before deeper analysis.

```
Rows: 2046851
Columns: 115
$ LOAN_ID                                            <str> '123137870847', '102157127407', '118628664860', '102993029045', '144572067909', '138444152104', '112817980899', '126148139122', '109759244771', '149125240859'
$ POOL_ID                                            <str> null, null, null, null, null, null, null, null, null, null
$ ACT_PERIOD                                         <str> '012017', '022017', '032017', '022017', '022017', '032017', '012017', '012017', '032017', '012017'
$ CHANNEL                                            <str> 'C', 'R', 'R', 'R', 'R', 'B', 'B', 'C', 'R', 'R'
$ SELLER                                             <str> 'Caliber Home Loans, Inc.', 'Quicken Loans Inc.', 'Other', 'Other', 'Other', 'Loandepot.Com, Llc', 'Other', 'Wells Fargo Bank, N.A.', 'Quicken Loans Inc.', 'Truist Bank (Formerly Suntrust Bank)'
$ SERVICER                                           <str> 'Other', 'Quicken Loans Inc.', 'Other', 'Other', 'Other', 'Other', 'Other', 'Wells Fargo Bank, N.A.', 'Quicken Loans Inc.', 'Suntrust Mortgage Inc.'
$ MASTER_SERVICER                                    <str> null, null, null, null, null, null, null, null, null, null
$ ORIG_RATE                                          <str> '4.375', '3.500', '4.625', '3.750', '3.250', '4.375', '3.750', '3.750', '3.875', '3.600'
$ CURR_RATE                                          <str> '4.375', '3.500', '4.625', '3.750', '3.250', '4.375', '3.750', '3.750', '3.875', '3.600'
$ ORIG_UPB                                           <str> '180000.00', '203000.00', '120000.00', '291000.00', '177000.00', '520000.00', '214000.00', '265000.00', '131000.00', '122000.00'
$ ISSUANCE_UPB                                       <str> null, null, null, null, null, null, null, null, null, null
$ CURRENT_UPB                                        <str> '0.00', '0.00', '0.00', '0.00', '0.00', '0.00', '0.00', '0.00', '0.00', '0.00'
$ ORIG_TERM                                          <str> '360', '360', '360', '240', '120', '360', '360', '360', '132', '360'
$ ORIG_DATE                                          <str> '122016', '012017', '022017', '012017', '112016', '022017', '122016', '112016', '022017', '122016'
$ FIRST_PAY                                          <str> '022017', '032017', '042017', '032017', '012017', '042017', '022017', '012017', '042017', '022017'
$ LOAN_AGE                                           <str> '0', '0', '0', '0', '2', '0', '0', '1', '0', '0'
$ REM_MONTHS                                         <str> '360', '360', '360', '240', '118', '360', '360', '359', '132', '360'
$ ADJ_REM_MONTHS                                     <str> '360', '360', '360', '239', '118', '360', '359', '359', '132', '359'
$ MATR_DT                                            <str> '012047', '022047', '032047', '022037', '122026', '032047', '012047', '122046', '032028', '012047'
$ OLTV                                               <str> '97', '41', '78', '67', '7
... [truncated]
```

```
shape: (2, 2)
┌──────────────┬─────────┐
│ default_flag ┆ count   │
│ ---          ┆ ---     │
│ i8           ┆ u32     │
╞══════════════╪═════════╡
│ 0            ┆ 1976965 │
│ 1            ┆ 69886   │
└──────────────┴─────────┘
```

## Loan Amount, State, and Zip Concentration Overview

This section establishes the baseline distribution facts needed to size the LP constraints. It covers three things: the loan amount summary (mean, median, and quartiles) to inform the budget figure, state-level concentration to inform the diversification cap, and zip-prefix concentration for finer geographic detail. Loan amounts are expressed as dollars and geographic shares as percentages of the full book, which matches the units the constraints will use.

```
Loan amount summary:
shape: (1, 6)
┌───────────────┬────────────┬─────────┬─────────┬──────────┬──────────┐
│ mean_upb      ┆ median_upb ┆ min_upb ┆ max_upb ┆ p25_upb  ┆ p75_upb  │
│ ---           ┆ ---        ┆ ---     ┆ ---     ┆ ---      ┆ ---      │
│ f64           ┆ f64        ┆ f64     ┆ f64     ┆ f64      ┆ f64      │
╞═══════════════╪════════════╪═════════╪═════════╪══════════╪══════════╡
│ 228839.312192 ┆ 206000.0   ┆ 5000.0  ┆ 1.223e6 ┆ 137000.0 ┆ 300000.0 │
└───────────────┴────────────┴─────────┴─────────┴──────────┴──────────┘

Number of distinct states: 54
State concentration (all, sorted):
shape: (54, 3)
┌───────┬────────┬──────┐
│ STATE ┆ count  ┆ pct  │
│ ---   ┆ ---    ┆ ---  │
│ str   ┆ u32    ┆ f64  │
╞═══════╪════════╪══════╡
│ CA    ┆ 280415 ┆ 13.7 │
│ TX    ┆ 164662 ┆ 8.04 │
│ FL    ┆ 141082 ┆ 6.89 │
│ AZ    ┆ 74413  ┆ 3.64 │
│ IL    ┆ 74134  ┆ 3.62 │
│ …     ┆ …      ┆ …    │
│ AK    ┆ 3237   ┆ 0.16 │
│ VT    ┆ 2646   ┆ 0.13 │
│ PR    ┆ 2449   ┆ 0.12 │
│ VI    ┆ 128    ┆ 0.01 │
│ GU    ┆ 77     ┆ 0.0  │
└───────┴────────┴──────┘

Number of distinct zip prefixes: 899
Top 10 zip prefixes by concentration:
shape: (10, 3)
┌─────┬───────┬──────┐
│ ZIP ┆ count ┆ pct  │
│ --- ┆ ---   ┆ ---  │
│ str ┆ u32   ┆ f64  │
╞═════╪═══════╪══════╡
│ 750 ┆ 26332 ┆ 1.29 │
│ 945 ┆ 22537 ┆ 1.1  │
│ 852 ┆ 21093 ┆ 1.03 │
│ 300 ┆ 20105 ┆ 0.98 │
│ 840 ┆ 17406 ┆ 0.85 │
│ 853 ┆ 16872 ┆ 0.82 │
│ 980 ┆ 15821 ┆ 0.77 │
│ 891 ┆ 14640 ┆ 0.72 │
│ 802 ┆ 14224 ┆ 0.69 │
│ 917 ┆ 14001 ┆ 0.68 │
└─────┴───────┴──────┘
```

## State Concentration with Cumulative Share and 4% Cap Check

This section builds on the state concentration view by adding a running cumulative share, so you can see how much of the portfolio the top states hold together. It also flags how many states currently exceed a 4% cap, which tells you at a glance how many would be actively constrained if you set the diversification limit there.

```
Top 10 states with cumulative share:
shape: (10, 4)
┌───────┬────────┬──────┬────────────────┐
│ STATE ┆ count  ┆ pct  ┆ cumulative_pct │
│ ---   ┆ ---    ┆ ---  ┆ ---            │
│ str   ┆ u32    ┆ f64  ┆ f64            │
╞═══════╪════════╪══════╪════════════════╡
│ CA    ┆ 280415 ┆ 13.7 ┆ 13.7           │
│ TX    ┆ 164662 ┆ 8.04 ┆ 21.74          │
│ FL    ┆ 141082 ┆ 6.89 ┆ 28.63          │
│ AZ    ┆ 74413  ┆ 3.64 ┆ 32.27          │
│ IL    ┆ 74134  ┆ 3.62 ┆ 35.89          │
│ WA    ┆ 72077  ┆ 3.52 ┆ 39.41          │
│ CO    ┆ 71785  ┆ 3.51 ┆ 42.92          │
│ MI    ┆ 67644  ┆ 3.3  ┆ 46.22          │
│ NC    ┆ 65230  ┆ 3.19 ┆ 49.41          │
│ NY    ┆ 62924  ┆ 3.07 ┆ 52.48          │
└───────┴────────┴──────┴────────────────┘

States over 4%: 3
shape: (3, 4)
┌───────┬────────┬──────┬────────────────┐
│ STATE ┆ count  ┆ pct  ┆ cumulative_pct │
│ ---   ┆ ---    ┆ ---  ┆ ---            │
│ str   ┆ u32    ┆ f64  ┆ f64            │
╞═══════╪════════╪══════╪════════════════╡
│ CA    ┆ 280415 ┆ 13.7 ┆ 13.7           │
│ TX    ┆ 164662 ┆ 8.04 ┆ 21.74          │
│ FL    ┆ 141082 ┆ 6.89 ┆ 28.63          │
└───────┴────────┴──────┴────────────────┘
```

## State Concentration and Risk

This section pairs geographic concentration with default rate at the state level. Sorting by portfolio share and showing each state's default rate side by side lets us see whether the largest states are also the riskiest, or whether concentration and risk move independently. That distinction matters for deciding how much work a state-level diversification cap does versus the average-PD ceiling.

```
Top 10 states: concentration vs risk
shape: (10, 3)
┌───────┬──────┬──────────────────┐
│ STATE ┆ pct  ┆ default_rate_pct │
│ ---   ┆ ---  ┆ ---              │
│ str   ┆ f64  ┆ f64              │
╞═══════╪══════╪══════════════════╡
│ CA    ┆ 13.7 ┆ 3.38             │
│ TX    ┆ 8.04 ┆ 4.61             │
│ FL    ┆ 6.89 ┆ 5.69             │
│ AZ    ┆ 3.64 ┆ 2.99             │
│ IL    ┆ 3.62 ┆ 4.1              │
│ WA    ┆ 3.52 ┆ 2.43             │
│ CO    ┆ 3.51 ┆ 2.26             │
│ MI    ┆ 3.3  ┆ 2.6              │
│ NC    ┆ 3.19 ┆ 2.64             │
│ NY    ┆ 3.07 ┆ 5.62             │
└───────┴──────┴──────────────────┘
```

## Zip Prefix Concentration and Risk Against a 0.50% Cap

This section looks at geographic concentration at the zip-prefix level and pairs it with default rate, so we can see both dimensions together. Filtering to prefixes above a 0.50% cap shows how many would be constrained and whether those dense pockets are actually riskier, or just larger. That tells us whether a zip-level cap would do meaningful risk work or mainly serve diversification.

```
Zip prefixes over 0.50%: 32 out of 899
shape: (32, 3)
┌─────┬───────┬──────────────────┐
│ ZIP ┆ pct   ┆ default_rate_pct │
│ --- ┆ ---   ┆ ---              │
│ str ┆ f64   ┆ f64              │
╞═════╪═══════╪══════════════════╡
│ 750 ┆ 1.286 ┆ 4.34             │
│ 945 ┆ 1.101 ┆ 2.96             │
│ 852 ┆ 1.031 ┆ 2.27             │
│ 300 ┆ 0.982 ┆ 3.82             │
│ 840 ┆ 0.85  ┆ 1.96             │
│ …   ┆ …     ┆ …                │
│ 334 ┆ 0.522 ┆ 6.14             │
│ 554 ┆ 0.516 ┆ 2.91             │
│ 982 ┆ 0.511 ┆ 2.68             │
│ 275 ┆ 0.507 ┆ 2.19             │
│ 928 ┆ 0.504 ┆ 3.04             │
└─────┴───────┴──────────────────┘
```

## Baseline Default Rates: Book-Level and by FICO Band

Before setting an average-PD ceiling, it helps to establish two reference points from the actual data. First, the book-level default rate, both amount-weighted (the form the LP constraint uses) and unweighted, to confirm they agree. Second, the default rate across standard FICO bands, which shows the underlying risk gradient and gives a feel for how much safe supply is available to draw from.

Note: this uses default_flag (actual outcomes) as a stand-in until the ML model produces predicted PD.

```
Amount-weighted average default rate (full book):
shape: (1, 1)
┌──────────────────────┐
│ wtd_avg_default_rate │
│ ---                  │
│ f64                  │
╞══════════════════════╡
│ 0.034982             │
└──────────────────────┘

Unweighted default rate: 3.41%
Default rate by standard FICO band:
shape: (6, 3)
┌─────────────────────┬────────┬──────────────────┐
│ fico_band           ┆ count  ┆ default_rate_pct │
│ ---                 ┆ ---    ┆ ---              │
│ str                 ┆ u32    ┆ f64              │
╞═════════════════════╪════════╪══════════════════╡
│ Exceptional (800+)  ┆ 308739 ┆ 0.88             │
│ Very Good (740-799) ┆ 967786 ┆ 1.98             │
│ Unknown (no score)  ┆ 1573   ┆ 2.8              │
│ Good (670-739)      ┆ 623257 ┆ 5.31             │
│ Fair (580-669)      ┆ 145495 ┆ 10.25            │
│ Poor (below 580)    ┆ 1      ┆ 100.0            │
└─────────────────────┴────────┴──────────────────┘
```

## Achievable Average Prob of Default (PD) at Different Selection Levels

This section helps ground the average-PD ceiling in real numbers. By sorting
loans safest-first and tracking the running amount-weighted default rate as we
fund more of the book, we can see which ceiling values are actually reachable
before picking one. (Using default_flag as a PD stand-in until the ML model
produces predicted probabilities.)

```
Funding safest 10% of loans -> avg PD: 0.88%
Funding safest 25% of loans -> avg PD: 1.08%
Funding safest 50% of loans -> avg PD: 1.51%
Funding safest 75% of loans -> avg PD: 2.22%
Funding safest 100% of loans -> avg PD: 3.50%
```

## LGD Feasibility Check: Recovery Data on Defaulted Loans

Before computing LGD from the Qi-Yang formula, we need to know whether the data
can even support it. The formula requires recovery fields that only populate
after a loan defaults, forecloses, and sells. This checks how many defaulted
loans actually have those fields populated. That count decides whether the
Qi-Yang and hybrid approaches are viable, or whether the Sirignano flat value
is the honest fallback.

```
Total defaulted loans: 69,886
NET_SALES_PROCEEDS                                  0 populated (0.0%)
FORECLOSURE_COSTS                                   0 populated (0.0%)
PROPERTY_PRESERVATION_AND_REPAIR_COSTS              0 populated (0.0%)
ASSET_RECOVERY_COSTS                                0 populated (0.0%)
LAST_UPB                                            0 populated (0.0%)
```

## Confirming Recovery Fields Are Empty Across the Full Book

A quick sanity check to rule out any chance the recovery fields were dropped or
renamed during reduction. If they are entirely null across all 2M loans, not
just the defaults, that confirms the fields simply do not carry into the
performance file, and the Qi-Yang formula genuinely cannot be applied here.

```
shape: (1, 5)
┌────────────────────┬───────────────────┬───────────────────────┬──────────────────────┬──────────┐
│ NET_SALES_PROCEEDS ┆ FORECLOSURE_COSTS ┆ PROPERTY_PRESERVATION ┆ ASSET_RECOVERY_COSTS ┆ LAST_UPB │
│ ---                ┆ ---               ┆ _AND_REPA…            ┆ ---                  ┆ ---      │
│ u32                ┆ u32               ┆ ---                   ┆ u32                  ┆ u32      │
│                    ┆                   ┆ u32                   ┆                      ┆          │
╞════════════════════╪═══════════════════╪═══════════════════════╪══════════════════════╪══════════╡
│ 2046851            ┆ 2046851           ┆ 2046851               ┆ 2046851              ┆ 2046851  │
└────────────────────┴───────────────────┴───────────────────────┴──────────────────────┴──────────┘

Total rows: 2,046,851
```

## Findings: LGD Cannot Be Computed From This Dataset

**Result:** All five recovery fields (NET_SALES_PROCEEDS, FORECLOSURE_COSTS,
PROPERTY_PRESERVATION_AND_REPAIR_COSTS, ASSET_RECOVERY_COSTS, LAST_UPB) are
null across all 2,046,851 loans, including all 69,886 defaulted loans.

**Implication:**
- The Qi-Yang (2007) formula is not computable here, since it requires realized
  recovery and expense figures that this performance file does not carry.
- The hybrid approach (deriving an average LGD from completed-sale loans) is
  also ruled out, as it depends on the same missing fields.

**Decision:** Adopt the Sirignano, Tsoukalas, and Giesecke (2016) flat-value
approach for LGD. Given the 2017 vintage sits in a stable housing period, a
normal-economy value (30 percent) is the baseline, with a downturn value
(50 percent) available for stress scenarios in the simulation stage.

**Justification:** This is an evidence-based fallback, not a shortcut. The
rigorous formula was tested against the data and found inapplicable due to
absent recovery fields, so the established peer-reviewed flat-value method is
the defensible alternative.

## LGD Scenarios: Normal (30%) vs Downturn (50%)

Applies the two Sirignano flat-value LGD assumptions to the book to see the
expected loss they imply per loan and in aggregate. This gives a concrete feel
for how much the choice of LGD matters before it feeds into expected return and
the simulation.

```
LGD = 30%
  Total expected loss:      $4,915,608,900
  Avg loss per loan:        $2,401.55
  Loss as % of total book:  1.05%

LGD = 50%
  Total expected loss:      $8,192,681,500
  Avg loss per loan:        $4,002.58
  Loss as % of total book:  1.75%
```

## Findings: Expected Loss Under Normal and Downturn LGD

**Setup:** Applied the two Sirignano flat-value LGD assumptions to the full
book. Expected loss per loan = PD * LGD * loan amount, using default_flag as
the PD stand-in until the model produces predicted PD.

**Results:**

| Scenario | LGD | Total Expected Loss | Avg Loss / Loan | Loss as % of Book |
|----------|-----|---------------------|-----------------|-------------------|
| Normal   | 30% | $4.92B              | $2,401.55       | 1.05%             |
| Downturn | 50% | $8.19B              | $4,002.58       | 1.75%             |

**Takeaways:**
- Actual capital loss (1.05% to 1.75%) sits well below the 3.4% default rate,
  since only a fraction of each defaulted balance is lost after recovery.
- The LGD choice introduces about 0.70 points of spread in book-level loss,
  a modest but real sensitivity.

**Decision:** Use 30% as the baseline for primary analysis, matching the stable
2017 housing period. Reserve 50% as a downturn stress scenario for the
simulation stage.

## Interest Rate Distribution

Summarizes ORIG_RATE across the book. This drives the return side of the
expected-return calculation, so understanding its central tendency and spread
sets up the LP stage.

```
Interest rate summary (%):
shape: (1, 7)
┌───────────┬─────────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ mean_rate ┆ median_rate ┆ min_rate ┆ max_rate ┆ p25_rate ┆ p75_rate ┆ std_rate │
│ ---       ┆ ---         ┆ ---      ┆ ---      ┆ ---      ┆ ---      ┆ ---      │
│ f64       ┆ f64         ┆ f64      ┆ f64      ┆ f64      ┆ f64      ┆ f64      │
╞═══════════╪═════════════╪══════════╪══════════╪══════════╪══════════╪══════════╡
│ 4.14      ┆ 4.125       ┆ 1.79     ┆ 6.125    ┆ 3.875    ┆ 4.5      ┆ 0.495    │
└───────────┴─────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

## Does Interest Rate Track Risk?

Groups loans by FICO band and shows the average interest rate alongside the
default rate for each. If rate rises as credit quality falls, it confirms the
risk-based pricing that the optimizer will navigate when trading return against
default risk.

```
Interest rate vs default risk by FICO band:
shape: (6, 4)
┌─────────────────────┬────────┬──────────┬──────────────────┐
│ fico_band           ┆ count  ┆ avg_rate ┆ default_rate_pct │
│ ---                 ┆ ---    ┆ ---      ┆ ---              │
│ str                 ┆ u32    ┆ f64      ┆ f64              │
╞═════════════════════╪════════╪══════════╪══════════════════╡
│ Poor (below 580)    ┆ 1      ┆ 3.625    ┆ 100.0            │
│ Exceptional (800+)  ┆ 308739 ┆ 3.97     ┆ 0.88             │
│ Very Good (740-799) ┆ 967786 ┆ 4.064    ┆ 1.98             │
│ Unknown (no score)  ┆ 1573   ┆ 4.199    ┆ 2.8              │
│ Good (670-739)      ┆ 623257 ┆ 4.262    ┆ 5.31             │
│ Fair (580-669)      ┆ 145495 ┆ 4.491    ┆ 10.25            │
└─────────────────────┴────────┴──────────┴──────────────────┘
```

## Findings: Interest Rate Distribution and Risk-Based Pricing

**Rate distribution:**
- Rates are tightly clustered. Mean 4.14%, median 4.13%, with the middle 50%
  falling between 3.875% and 4.5% (std 0.495). Full range is 1.79% to 6.125%.
- The return side of the book varies little from loan to loan.

**Rate vs risk by FICO band** (Poor band holds a single loan and is excluded;
no-score loans are shown separately below):

| FICO Band            | Count   | Avg Rate | Default Rate |
|----------------------|---------|----------|--------------|
| Exceptional (800+)   | 308,739 | 3.97%    | 0.88%        |
| Very Good (740-799)  | 967,786 | 4.06%    | 1.98%        |
| Good (670-739)       | 623,257 | 4.26%    | 5.31%        |
| Fair (580-669)       | 145,495 | 4.49%    | 10.25%       |

**Key takeaway:**
- Pricing tracks risk, but weakly. From Exceptional to Fair, rate rises about
  0.5 points while default rate climbs more than elevenfold.
- The extra interest on riskier loans does not compensate for the added default
  risk. Safer loans likely carry higher expected return once loss is netted out.

**The no-score loans are worth keeping.** 1,573 loans have no FICO at all. They
priced at 4.199%, between Good and Fair, but defaulted at only 2.8%, better than
Good. Lenders treated them as moderately risky and they outperformed that. Small
group, but it argues for carrying them with a missing-score flag rather than
dropping them.

## Future Impact: Remaining Project

**ML stage:**
- FICO is a strong, clean predictor of default, which supports its weight as a
  feature. The steep risk gradient means the model has real signal to learn.
- Rate is priced off the same risk the model is trying to predict, and the near-flat
  rate gradient against an elevenfold default gradient shows how little independent
  signal it carries. This is the case for keeping ORIG_RATE out of the feature set
  and using it only for the LP income calculation.

**LP stage:**
- Expected return will likely favor high-FICO loans, since their low default
  cost barely dents a rate similar to riskier loans. The optimizer may lean
  toward the safest segment on its own.
- This is what makes the average-PD ceiling and diversification caps meaningful.
  Without them, the portfolio could pile into low-risk loans and lose realism.
  With them, the constraints force a more balanced, defensible allocation.

**Simulation stage:**
- The lopsided risk-return structure sets up a clear contrast between the
  optimized portfolio and the naive baseline.

### Primary sources worth citing:

* OCC Comptroller's Handbook, Concentrations of Credit (Version 2.0, October 2020)
* OCC Comptroller's Handbook, Loan Portfolio Management (April 1998)
* 12 CFR 32 and 12 USC 84 (national bank lending limits)
* FFIEC Interagency Guidance on Concentrations in Commercial Real Estate (2006)

## First-Time Homebuyer Share of the Book

Uses FIRST_FLAG (Y or N) to see how many loans went to first-time homebuyers,
and pairs it with default rate to check whether that group carries different
risk. This may inform whether first-time buyer status is worth including as a
feature or constraint dimension later.

```
First-time homebuyer breakdown:
shape: (2, 4)
┌────────────┬─────────┬──────────────────┬─────────────┐
│ FIRST_FLAG ┆ count   ┆ default_rate_pct ┆ pct_of_book │
│ ---        ┆ ---     ┆ ---              ┆ ---         │
│ str        ┆ u32     ┆ f64              ┆ f64         │
╞════════════╪═════════╪══════════════════╪═════════════╡
│ N          ┆ 1558365 ┆ 2.97             ┆ 76.13       │
│ Y          ┆ 488486  ┆ 4.83             ┆ 23.87       │
└────────────┴─────────┴──────────────────┴─────────────┘
```

## Check for Income or Affordability Fields

Scans the dataset for any column that could carry income, area median income,
or affordability signal. Fannie Mae's public loan performance file is known to
omit borrower income, so this confirms what we do and do not have before
deciding whether an income-based constraint is even possible.

```
Columns matching income/affordability terms:
None found

HomeReady program indicator value counts:
shape: (3, 2)
┌─────────────────────────────┬─────────┐
│ HOMEREADY_PROGRAM_INDICATOR ┆ count   │
│ ---                         ┆ ---     │
│ str                         ┆ u32     │
╞═════════════════════════════╪═════════╡
│ 7                           ┆ 1890786 │
│ H                           ┆ 103860  │
│ F                           ┆ 52205   │
└─────────────────────────────┴─────────┘
```

## Default Rates for Affordable-Program Loans

Compares default rates across the HomeReady program indicator (H = HomeReady,
F = HFA Preferred, 7 = Not applicable). This shows the risk tradeoff of an
affordable-program floor, the same way we checked first-time buyers.

```
Default rate by affordable-program flag:
shape: (3, 4)
┌─────────────────────────────┬─────────┬──────────────────┬─────────────┐
│ HOMEREADY_PROGRAM_INDICATOR ┆ count   ┆ default_rate_pct ┆ pct_of_book │
│ ---                         ┆ ---     ┆ ---              ┆ ---         │
│ str                         ┆ u32     ┆ f64              ┆ f64         │
╞═════════════════════════════╪═════════╪══════════════════╪═════════════╡
│ 7                           ┆ 1890786 ┆ 3.12             ┆ 92.38       │
│ H                           ┆ 103860  ┆ 5.92             ┆ 5.07        │
│ F                           ┆ 52205   ┆ 9.21             ┆ 2.55        │
└─────────────────────────────┴─────────┴──────────────────┴─────────────┘
```

## Average Loan Size by Affordable-Program Flag

Compares loan amounts across the HomeReady indicator (H, F, and 7) to see
whether affordable-program loans skew smaller. This informs whether a floor
constraint should be framed as a percent of loan count or a percent of budget
dollars.

```
Loan size by affordable-program flag:
shape: (3, 5)
┌─────────────────────────────┬─────────┬──────────┬────────────┬─────────────┐
│ HOMEREADY_PROGRAM_INDICATOR ┆ count   ┆ mean_upb ┆ median_upb ┆ pct_of_book │
│ ---                         ┆ ---     ┆ ---      ┆ ---        ┆ ---         │
│ str                         ┆ u32     ┆ f64      ┆ f64        ┆ f64         │
╞═════════════════════════════╪═════════╪══════════╪════════════╪═════════════╡
│ 7                           ┆ 1890786 ┆ 233023.0 ┆ 212000.0   ┆ 92.38       │
│ H                           ┆ 103860  ┆ 181585.0 ┆ 165000.0   ┆ 5.07        │
│ F                           ┆ 52205   ┆ 171340.0 ┆ 161000.0   ┆ 2.55        │
└─────────────────────────────┴─────────┴──────────┴────────────┴─────────────┘
```

## Findings: Socio-Economic Constraint Options

Explored two dimensions in the data that support a socio-economic floor
constraint: first-time homebuyer status (FIRST_FLAG) and affordable-program
participation (HOMEREADY_PROGRAM_INDICATOR). Borrower income is not present in
the Fannie Mae public file, so these two flags are the usable socio-economic
signals.

### First-Time Homebuyers (FIRST_FLAG)

| Group | Share of Book | Default Rate |
|-------|---------------|--------------|
| First-time buyer (Y) | 23.87% | 4.83% |
| Repeat buyer (N)     | 76.13% | 2.97% |

- Broad, well-supplied signal. Higher risk than repeat buyers, but plenty of
  supply for the optimizer to draw from.

### Affordable Programs (HOMEREADY_PROGRAM_INDICATOR)

| Program | Share of Book | Default Rate | Median Loan |
|---------|---------------|--------------|-------------|
| HomeReady (H)      | 5.07% | 5.92% | $165,000 |
| HFA Preferred (F)  | 2.55% | 9.21% | $161,000 |
| Standard (7)       | 92.38% | 3.12% | $212,000 |

- Smaller, sharper signal. These are income-targeted programs, so they map more
  directly to affordable-lending intent, but carry steeper default risk and
  limited supply.
- Notable finding: HFA Preferred defaults at nearly triple the standard rate,
  meaningfully higher than HomeReady. Not all affordable programs perform the
  same, which is worth reporting rather than hiding by combining them.
- Affordable-program loans run 20 to 25% smaller in balance, so a count-based
  floor consumes less budget than expected. Serving these borrowers costs less
  capacity than it appears.

### Recommendations

- **Keep the two dimensions separate.** First-time buyer and affordable-program
  status capture different things (buyer experience vs income-targeted product),
  and separating them preserves the finding that programs differ in return.
- **Frame floors as a percent of loan count, not budget dollars.** The goal is
  reaching borrowers, which is about people served, not capital deployed. Count
  framing also lets the smaller loan sizes work in your favor.
- **Suggested starting ranges** (to vary in sensitivity analysis, not lock):
  - First-time buyer floor: 25 to 30 percent of funded loans (natural share 23.87 percent)
  - HomeReady (H) floor: 5 to 7 percent of funded loans (natural share 5.07 percent)
  - HFA Preferred (F) floor: 2.5 to 3.5 percent of funded loans (natural share 2.55 percent)

### Suggested Approach

Rather than fixing single values, vary each floor across a small range and
observe how objective of expected return responds. This turns the "not all programs are
equal" insight into a measurable result, showing HFA Preferred costs more return
per unit of floor than HomeReady. That contrast supports the central thesis:
socio-economic consideration and profitability can coexist, with a cost that is
visible and manageable.

## Notebook Summary: Takeaways for Future Stages

### For the ML Stage
- FICO is a strong, clean predictor of default. Rate climbs smoothly from 0.88%
  (Exceptional) to 10.25% (Fair), giving the model real signal.
- FIRST_FLAG carries signal: first-time buyers default at 4.83% vs 2.97% for
  repeat buyers.
- HOMEREADY_PROGRAM_INDICATOR carries signal: HomeReady (H) defaults at 5.92%,
  HFA Preferred (F) at 9.21%, vs 3.12% standard.
- Target is imbalanced at 3.4% default, which the modeling approach must account
  for (metrics, class weighting).

### For the LP Stage
- Budget sizing: mean loan 229k, median 206k, middle 50% between 137k and 300k.
- State concentration matters most for diversification. CA holds 13.7%, but
  concentration and risk do not align (FL, TX, NY are the risky large states;
  CA, WA, CO are safe). This argues for pairing a diversification cap with the
  average-PD ceiling, since each does a different job.
- Zip concentration is diffuse (no prefix above 1.3%), so a zip cap is a soft
  lever compared to state.
- Average-PD ceiling: achievable floor is ~0.88% (safest 10%), rising to 3.5%
  (full book). Meaningful ceiling range is roughly 1% to 3.4%.
- LGD cannot be computed from this data (all recovery fields null across the
  book). Use Sirignano flat values: 30% baseline, 50% downturn stress.
- Interest rates are tightly clustered (mean 4.14%, most between 3.875% and
  4.5%), and rise only ~0.5 points from safest to riskiest FICO band while
  default rises elevenfold. Safe loans likely carry higher expected return, so
  constraints are what force a realistic, diversified portfolio.

### Socio-Economic Constraints (count-based floors, kept separate)
- First-time buyer: 23.87% of book, suggested floor 25-30%.
- HomeReady (H): 5.07% of book, suggested floor 5-7%.
- HFA Preferred (F): 2.55%

## Before and After: One Loan, Many Rows to One Row

To show what the reduction actually does, we take a single loan and follow it
through the process. In the raw file this loan appears once per month, so its
origination facts (like the borrower FICO score) simply repeat, while its
delinquency status changes over time. After the reduction, those monthly rows
collapse into one. The repeating facts are kept once, and the changing
delinquency column becomes two things: the worst delinquency the loan ever
reached, and the final default flag.

```
Example loan: 133094666195
```

```
Raw rows for this loan: 107
```

```
shape: (6, 5)
┌──────────────┬────────────┬──────────┬────────────┬───────────────┐
│ LOAN_ID      ┆ ACT_PERIOD ┆ CSCORE_B ┆ DLQ_STATUS ┆ Zero_Bal_Code │
│ ---          ┆ ---        ┆ ---      ┆ ---        ┆ ---           │
│ str          ┆ str        ┆ str      ┆ str        ┆ str           │
╞══════════════╪════════════╪══════════╪════════════╪═══════════════╡
│ 133094666195 ┆ 012018     ┆ 738      ┆ 00         ┆ null          │
│ 133094666195 ┆ 012019     ┆ 738      ┆ 00         ┆ null          │
│ 133094666195 ┆ 012020     ┆ 738      ┆ 00         ┆ null          │
│ 133094666195 ┆ 012021     ┆ 738      ┆ 00         ┆ null          │
│ 133094666195 ┆ 012022     ┆ 738      ┆ 00         ┆ null          │
│ 133094666195 ┆ 012023     ┆ 738      ┆ 00         ┆ null          │
└──────────────┴────────────┴──────────┴────────────┴───────────────┘
```

```
shape: (1, 5)
┌──────────────┬──────────┬──────────────┬───────────────┬──────────────┐
│ LOAN_ID      ┆ CSCORE_B ┆ max_dlq_ever ┆ zero_bal_code ┆ default_flag │
│ ---          ┆ ---      ┆ ---          ┆ ---           ┆ ---          │
│ str          ┆ str      ┆ i32          ┆ str           ┆ i8           │
╞══════════════╪══════════╪══════════════╪═══════════════╪══════════════╡
│ 133094666195 ┆ 738      ┆ 0            ┆ null          ┆ 0            │
└──────────────┴──────────┴──────────────┴───────────────┴──────────────┘
```

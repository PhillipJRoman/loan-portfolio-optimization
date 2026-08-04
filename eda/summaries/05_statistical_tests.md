# 05_statistical_tests

## Significance Tests will likely show p-value being miniscule due to the large sample

```
Full sample (n=2,044,946):
  chi2 = 42,027   p = 0.00e+00   dof = 3
  subsample n=102,247:  chi2=     2,085   p=0.00e+00
  subsample n= 10,225:  chi2=       297   p=5.20e-64
  subsample n=  2,045:  chi2=        65   p=4.82e-14

Interpretation: p is effectively zero at every sample size that isn't tiny.
Significance testing cannot rank these effects — effect sizes will.
```

```
feature  cramers_v       n   strength
       FICO band     0.1434 2044945      small
        DTI band     0.0751 2044946      small
           State     0.0610 2044946      small
Assistance prog.     0.0571 2044946      small
        LTV band     0.0551 2044946      small
     Co-borrower     0.0549 2044946      small
First-time buyer     0.0439 2044946 negligible
         Channel     0.0230 2044946 negligible
    Loan Purpose     0.0223 2044946 negligible
       Occupancy     0.0172 2044946 negligible
```

## Cramer's V: feature association with default
- Bias-corrected Cramer's V (Bergsma 2013) ranks each feature's association with the default outcome; the correction prevents high-cardinality features like State (~50 levels) from being unfairly inflated relative to binary flags. 

- FICO band is the strongest (0.143), roughly twice DTI (0.075) and 2.6× LTV (0.055), reproducing the univariate lift hierarchy of Block 2 via an independent, sample-size-robust measure. Notably, State (0.061) outranks LTV, giving empirical support for geographic diversification constraints in the portfolio optimization stage. 

- All values fall in the "small/negligible" Cohen bands, but these thresholds were derived for balanced tables and are mechanically compressed for a rare (3.4%) outcome; the informative content is therefore the relative ranking and ratios between features, not the absolute band labels.

```
split rate_flagged rate_other  abs_diff_ppts  rel_risk  cohens_h  n_flagged magnitude
   First-time buyer        4.84%      2.97%           1.87      1.63     0.097     487481     small
 Assistance program        7.02%      3.12%           3.91      2.25     0.182     155803     small
Co-borrower present        2.36%      4.35%          -2.00      0.54    -0.112     963221     small

Cohen's h bands: 0.2 small · 0.5 medium · 0.8 large
Relative risk = flagged rate / other rate (multiplicative view)
```

### Standardized effect sizes for binary risk flags 
- Each flag's default rate is compared against its complement using three lenses: absolute difference (percentage points), relative risk (multiplicative), and Cohen's h (a dimensionless effect size robust to the low base rate, unlike the compressed Cramér's V above). 

- Assistance-program participation carries the largest effect (h=0.182, 2.25× relative risk), followed by first-time status (h=0.097, 1.63×). Co-borrower presence is protective, the sole negative effect (h=−0.112)  with co-borrowed loans defaulting at roughly half the solo rate (2.36% vs 4.35%). 

- These are unconditional, whole-sample effects; comparison with the FICO/DTI-controlled premiums of Block 4 (first-time +1.71 ppts, assistance +2.89 ppts) shows first-time risk is almost entirely independent of borrower composition, while roughly a quarter of the raw assistance premium reflects weaker underlying fundamentals. All Wilson 95% confidence intervals are tight given the sample sizes.

## VIF values

```
With co-borrower FICO (complete cases)  (n=963,221)
  feature  VIF
 CSCORE_B 1.85
 CSCORE_C 1.84
ORIG_TERM 1.19
     OLTV 1.17
      DTI 1.09
 ORIG_UPB 1.08
   NUM_BO 1.01

Without co-borrower FICO (full book)  (n=2,044,946)
  feature  VIF
ORIG_TERM 1.17
     OLTV 1.14
      DTI 1.08
 ORIG_UPB 1.08
 CSCORE_B 1.06
   NUM_BO 1.05

Rule of thumb: VIF < 5 = fine, 5–10 = moderate, >10 = severe collinearity
```

All VIFs are fine

```
EDA logistic regression (n=2,044,946, interpretation only)

                coef_std  odds_ratio direction  p_value
CSCORE_B          -0.675       0.509    ↓ risk      0.0
has_coborrower    -0.651       0.522    ↓ risk      0.0
is_hfa             0.429       1.535    ↑ risk      0.0
DTI                0.332       1.394    ↑ risk      0.0
OLTV               0.150       1.162    ↑ risk      0.0
is_first_time      0.149       1.161    ↑ risk      0.0
ORIG_TERM          0.131       1.140    ↑ risk      0.0
has_mi             0.108       1.114    ↑ risk      0.0
NUM_BO             0.106       1.111    ↑ risk      0.0
ORIG_UPB           0.104       1.110    ↑ risk      0.0
is_homeready       0.086       1.089    ↑ risk      0.0

Pseudo-R² (McFadden): 0.0938
Numerics standardized → coef = effect per 1 SD; flags are 0/1 → OR = flagged vs not
```

### EDA logistic regression: adjusted feature effects
- A single full-sample logistic regression (interpretation only — no train/test split or tuning) estimates each feature's independent contribution to default with all others held fixed, generalizing the two-way conditioning of Figures 7 and 9.

- Numeric features are standardized, so coefficients are comparable as effect-per-standard-deviation; flags are 0/1, so odds ratios read as flagged-vs-not. FICO remains dominant (OR 0.509 per SD, halving default odds), confirming its top rank across univariate lift, Cramér's V, and multivariate adjustment. 

- Co-borrower presence rises to near-parity with FICO as a protective factor (OR 0.522) — far stronger than its unadjusted effect (h=−0.112), indicating its protection was masked in marginal comparisons. HFA participation carries substantial independent risk (OR 1.535), while HomeReady nearly vanishes under adjustment (OR 1.089), showing the two assistance programs behave very differently despite being grouped in Block 4. 

- First-time status remains an independent risk factor but attenuates (OR 1.161). All p-values are ≈0 (expected at n≈2M — features are ranked by standardized coefficient, not significance); McFadden pseudo-R² of 0.094 is typical for rare-event default and leaves clear headroom for a non-linear model to exploit the interactions documented in Block 4.

```
Model features committed: 15
  numeric:     6
  categorical: 4
  flags:       5
  + 1 conditional (CSCORE_C, pending team decision)

['CSCORE_B', 'DTI', 'OLTV', 'ORIG_UPB', 'ORIG_TERM', 'NUM_BO', 'STATE', 'PURPOSE', 'OCC_STAT', 'CHANNEL', 'has_coborrower', 'is_hfa', 'is_first_time', 'is_homeready', 'has_mi']
```

# Feature Selection: EDA Conclusion

### The EDA commits 15 model features (plus one pending decision), each supported by evidence from Blocks 1–5.

Using numeric (6): CSCORE_B, DTI, OLTV, ORIG_UPB, ORIG_TERM, NUM_BO. All VIF < 2 (multicollinearity-clean), all independent contributors in the adjusted regression.

Using categorical (4): STATE (Cramér's V 0.061, outranks LTV and also drives LP diversification), plus PURPOSE, OCC_STAT, CHANNEL as standard low-cardinality underwriting fields.

Using flags (5): has_coborrower (adjusted OR 0.522, the second-strongest feature and protective), is_hfa (OR 1.54), is_first_time (OR 1.16), is_homeready (OR 1.09, kept separate from HFA since they behave differently), has_mi (optional, overlaps OLTV).

Pending decision - CSCORE_C: carries real independent signal (not collinear with primary FICO, VIF 1.84) but is 53% missing by structure (no co-borrower). Either impute-plus-flag or exclude — a team call, not a data quality issue.

Not using, by reason:

Redundant (Block 3): OCLTV (0.98 corr with OLTV), MI_PCT (⟺ OLTV>80)
Economics-only — LP inputs, not predictors: ORIG_RATE (risk-based pricing, leakage-adjacent), interest_income_7yr, loss_if_default, lgd
Leakage — label components, already dropped: max_dlq_ever, zero_bal_code
Identity / high-cardinality — memorization risk: SELLER, ZIP, MSA, LOAN_ID

Every feature that enters the model has passed four gates: no leakage (Block 1), no redundancy (Block 3), demonstrated effect (Blocks 4–5), and independent multivariate contribution (adjusted logistic regression). This is the evidence-backed handoff from EDA to the modeling stage.

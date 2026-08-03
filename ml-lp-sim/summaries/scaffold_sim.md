# scaffold_sim

## Stage 4, piece 1: independent-draw simulation

**What this does:** for each of the six portfolios, we roll the dice 10,000 times.
Each roll is one simulated year. In a year, every funded loan either defaults or
survives, decided by its own default risk, independently of the others. We collect
interest on survivors, subtract losses on defaulters, and get that year's return
per dollar. Ten thousand years gives a spread of outcomes per portfolio.

**Independent means each loan's coin flip is on its own.** No shared economy yet.
This is the simple baseline. Its known weakness: with thousands of loans flipping
independently, the good and bad average out, so almost every year lands near the
expected return and the tail is thin. That is expected. Piece 2 adds the shared
economy that makes bad years cluster.

**The three metrics:**
- average return: the typical year. Should land near the LP's expected return.
- spread: how much returns bounce year to year. The simplest risk measure.
- bad year (5th percentile): the return in a year worse than 95% of years. First
  look at the downside.

**Fractional loans handled proportionally:** a loan funded at 40% contributes 40%
of its interest and 40% of its loss.

**LGD is 30%,** the Sirignano base case, already in the `loss_if_default` column.

```
score     rule             avg %   spread  bad yr %
FICOxLTV  risk-sort       25.30   0.016    25.27
FICOxLTV  greedy-return   30.72   0.035    30.66
FICOxLTV  LP              30.51   0.033    30.45
CatBoost  risk-sort       24.73   0.009    24.72
CatBoost  greedy-return   30.89   0.025    30.85
CatBoost  LP              30.64   0.023    30.61
```

## Finding: independent draws are unrealistically calm

Baseline simulation, 10,000 years, each loan defaulting on its own.

| Score | Rule | avg % | spread | bad year % |
|---|---|---|---|---|
| CatBoost | greedy-return | 30.89 | 0.025 | 30.85 |
| CatBoost | LP | 30.64 | 0.023 | 30.61 |
| FICO×LTV | greedy-return | 30.72 | 0.035 | 30.66 |
| FICO×LTV | LP | 30.51 | 0.033 | 30.45 |
| FICO×LTV | risk-sort | 25.30 | 0.016 | 25.27 |
| CatBoost | risk-sort | 24.73 | 0.009 | 24.72 |

**The spread is nearly zero.** Every simulated year lands within a few hundredths
of a percent of the average. The bad year sits right on top of the average
everywhere. Nothing bad ever happens.

**Why:** when thousands of loans each flip their own coin, the good and bad cancel
out. The law of averages crushes the year-to-year variation to almost nothing.

**Two checks pass:**
- Average returns match the LP's expected returns, so the simulation is wired
  right.
- The ordering is sensible: greedy-return and LP earn most, risk-sort least.

**Why this matters:** independent draws hide the entire point of the project. The
LP's spread across states and greedy-return's concentration look identical here,
because independence cannot see that loans default together in bad years. Piece 2
adds a shared economy so bad years cluster, which is where the portfolios finally
separate.

# Stage 4, part 2: correlated defaults simulation

## Why part 1 was not enough

In part 1, each loan defaulted or survived on its own, with no connection to any
other loan. Across thousands of loans the good and bad canceled out, so the
results for every simulated year landed within a few hundredths of a percent of
the average. Nothing bad ever happened.

That result is not realistic. Mortgages default in clusters: a recession hits,
home prices fall, and many borrowers go under at the same time for the same
reason. Part 1 cannot produce that, so it cannot test whether our diversification
and equity constraints are worth anything.

## What we are adding

**Reference:** Vasicek, O. A. (1987). *Probability of Loss on Loan Portfolio*.
KMV Corporation. Vasicek's single-factor model is what bank regulators built the
Basel II/III capital rules on. It is the standard way to model loans defaulting
together, and the 0.15 asset correlation (Basel rate) we use for mortgages comes from those
same Basel rules.

The model gives each loan two sources of possible default instead of one.

- **The systematic factor (the economy's luck).** One random number per simulated
  year, shared by every loan that year. A bad draw is a recession, a good draw is a
  boom.
- **The idiosyncratic factor (the loan's own luck).** One random number per loan
  per year. This is borrower-specific (individual) trouble: job loss, divorce,
  medical bills, events that affect one borrower and not the other.

Both are needed. With only the systematic factor, every loan of the same risk
would share an identical fate: all default or all survive. That is not clustering,
that is cloning. The idiosyncratic factor is what lets some 5% loans default in a
bad year while others do not.

## How a default is decided, step by step

1. Draw one systematic factor per year. 10,000 numbers.
2. Draw one idiosyncratic factor per loan per year. 10,000 x 409,926 numbers.
3. Combine them into a latent score for each loan in each year:

   `score = sqrt(0.15) x systematic + sqrt(0.85) x idiosyncratic`

4. Give each loan a default threshold based on its own predicted default rate. A
   loan CatBoost put at 5% gets `norm.ppf(0.05)` = -1.645. (This is a z-score: the
   number of standard deviations below the mean at which 5% of the distribution
   falls.)
5. The loan defaults that year if the loan's score falls below its default threshold.
6. Then, add up interest on the survivors, subtract losses on the defaulters,
   divide by dollars funded. That is the year's return.
7. Repeat for 10,000 years (simulations), then measure the final results.

## Two things worth understanding about the math

**The asset correlation is only a mixing ratio.** It decides how much of the score
comes from the systematic factor versus the idiosyncratic factor. At 0 it is all
idiosyncratic, which is part 1. At 1 it is all systematic, which is the cloning
problem. At asset correlation of 0.15, 15% of the variance comes from the economy.

**Each loan keeps its own risk.** The square roots are there so the variances add
to 1 (0.15 + 0.85), which keeps the score on the same standard normal scale as the
two inputs. That means the default threshold stays valid whatever we set the asset
correlation to. A loan with a predicted probability of default (PD) of 5% still
defaults 5% of the time. We are only changing how many of those defaults land in
the same year.

## Where the bad years come from

When the systematic factor draws a bad number, every loan's score drops by the
same amount at once. Loans that would normally squeak past their threshold now
fall below it. Instead of the usual 3.4% defaulting, maybe 10% do. That pile-up is
the bad year part 1 could never produce, and it is what our constraints exist to
survive.

## Metrics

Three metrics from part 1:
- average return
- spread (standard deviation), how much returns move year to year
- bad year, the return at the 5th percentile (Value at Risk)

Two additional metrics used in part 2, which help explore the impacts of bad
years:
- worst-years average, the average return across the worst 5% of years (Expected
  Shortfall, or CVaR)
- chance of a losing year, how often the portfolio returns below zero

## Plan for part 2

1. **Base run.** Asset correlation of 0.15, six portfolios assessed, five metrics measured. See whether
   the portfolios finally separate.
2. **Vary the asset correlation.** Run 0.0, 0.15, and 0.30. Shows how much the
   answer depends on that one number. The 0.0 run should reproduce part 1, which
   also confirms the code is correct.
3. **Stress the loss rate.** Our loss given default (LGD) is a flat 30% following
   Sirignano. Bad years hurt recovery too, so we also run 50% as a downturn case.
4. **Findings, then save.**

## Verify the simulation mechanism

Before running all six portfolios, confirm the model does what we claim.

**Three checks:**
- The latent score is standard normal (mean 0, standard deviation 1). This is what
  makes the default threshold valid.
- A loan with a 5% PD defaults about 5% of the time.
- Defaults cluster. The yearly default rate should swing widely instead of sitting
  flat like part 1.

If any check fails, every number downstream is wrong.

```
--- check 1: score is standard normal ---
  mean -0.0058  (expect ~0)
  std  1.0007  (expect ~1)

--- check 2: a 5% loan defaults 5% of the time ---
  threshold        -1.6449
  overall default  0.0507  (expect ~0.0500)

--- check 3: defaults cluster ---
  yearly rate min  0.0000
  yearly rate max  0.4526
  yearly rate std  0.0448
  5th pct year     0.0068
  95th pct year    0.1376
```

## Finding: the correlated model works, and bad years now exist

Test on 5,000 loans at 5% PD, 10,000 years, asset correlation 0.15.

**All three checks pass:**

| Check | Result | Expected |
|---|---|---|
| Score mean | -0.0058 | ~0 |
| Score standard deviation | 1.0007 | ~1 |
| Overall default rate | 5.07% | 5.00% |

The score is standard normal, so the default threshold is valid. Each loan keeps
its own predicted risk.

**Defaults now cluster.** Each simulated year, some share of the 5,000 loans
defaults. Below is where those yearly rates land across all 10,000 years:

| | Yearly default rate |
|---|---|
| Best year | 0.00% |
| 5th percentile (better than 95% of years)| 0.68% |
| Average year | 5.07% |
| 95th percentile (worse than 95% of years)| 13.76% |
| Worst year | 45.26% |

The 95th percentile year is 20 times worse than the 5th percentile year. The worst
year is 9 times the average. In part 1 the same spread was a few hundredths of a
percent.

**The shape matters.** Most years are calm and a small number of terrible years
pull the average up. That is the real pattern in mortgage credit.

## Impact on the project

- **Our constraints can finally be tested.** The state cap and equity floors cost
  us $21.9M in expected return. Part 1 could not show whether that bought anything
  because no portfolio ever had a bad year. Now they can be judged on how they hold
  up when defaults pile up.

- **Expected return alone was never going to settle the argument.** The 2x3
  ablation ranked greedy-return first because it earns the most on paper. That
  ranking assumes the average year. With bad years in the model, the ranking may
  change.

- **The two additonal metrics now have something to measure.** Worst-years average and
  chance of a losing year were meaningless in part 1. They are the metrics that
  test the central claim.

- **This is the setup for the real test.** The next run puts all six portfolios
  through these same bad years and shows which ones survive.

## Setup

Load the six portfolios and pull out the arrays the simulation needs.

```
loans      : 409,926
portfolios : 6
  x__FICOxLTV__risk-sort
  x__FICOxLTV__greedy-return
  x__FICOxLTV__LP
  x__CatBoost__risk-sort
  x__CatBoost__greedy-return
  x__CatBoost__LP
```

## Base run: six portfolios, correlated defaults

Asset correlation 0.15, LGD 30%, 10,000 simulated years.

**Chunked in batches of 500 years.** The full draw matrix would need roughly 33 GB.
Processing 500 years at a time keeps peak memory near 2.5 GB. All six portfolios
face the identical years within each chunk, so the comparison is fair.

**Progress prints per chunk** so a stall is visible.

**Saves** per-year returns to parquet and the five metrics to JSON, both tagged
with a run label so later runs append to the same files.

```
chunk  1/20  years     0-  500     0.8s
  chunk  2/20  years   500- 1000     1.4s
  chunk  3/20  years  1000- 1500     2.1s
  chunk  4/20  years  1500- 2000     2.8s
  chunk  5/20  years  2000- 2500     3.4s
  chunk  6/20  years  2500- 3000     4.1s
  chunk  7/20  years  3000- 3500     4.8s
  chunk  8/20  years  3500- 4000     5.4s
  chunk  9/20  years  4000- 4500     6.1s
  chunk 10/20  years  4500- 5000     6.8s
  chunk 11/20  years  5000- 5500     7.5s
  chunk 12/20  years  5500- 6000     8.1s
  chunk 13/20  years  6000- 6500     8.8s
  chunk 14/20  years  6500- 7000     9.5s
  chunk 15/20  years  7000- 7500    10.1s
  chunk 16/20  years  7500- 8000    10.8s
  chunk 17/20  years  8000- 8500    11.5s
  chunk 18/20  years  8500- 9000    12.1s
  chunk 19/20  years  9000- 9500    12.8s
  chunk 20/20  years  9500-10000    13.5s

done in 13.5s

asset correlation 0.15   LGD 30%   10,000 simulated years
All values are RETURN on dollars funded, except the last column.

score     rule           avg return  std dev  bad-yr return  worst-yrs return  yrs w/ loss
                          (typical)    (pts)   (5th pctile)    (avg worst 5%) (% of years)
--------------------------------------------------------------------------------------------
FICOxLTV  risk-sort          25.30%    0.32         24.71%            24.27%        0.00%
FICOxLTV  greedy-return      30.72%    1.04         28.67%            27.63%        0.00%
FICOxLTV  LP                 30.51%    1.05         28.46%            27.40%        0.00%
CatBoost  risk-sort          24.73%    0.15         24.47%            24.23%        0.00%
CatBoost  greedy-return      30.89%    0.72         29.49%            28.66%        0.00%
CatBoost  LP                 30.65%    0.71         29.26%            28.44%        0.00%

saved sim_returns.parquet and sim_summary.json  (run: base_rho015_lgd30)
```

## Finding: correlation works, but the ranking does not change

Asset correlation 0.15, LGD 30%, 10,000 simulated years. All values are return on
dollars funded, except the last column.

| Score | Rule | avg return | std dev | bad-yr return | worst-yrs return | yrs w/ loss |
|---|---|---|---|---|---|---|
| CatBoost | greedy-return | 30.89% | 0.72 | 29.49% | 28.66% | 0.00% |
| CatBoost | LP | 30.65% | 0.71 | 29.26% | 28.44% | 0.00% |
| FICO×LTV | greedy-return | 30.72% | 1.04 | 28.67% | 27.63% | 0.00% |
| FICO×LTV | LP | 30.51% | 1.05 | 28.46% | 27.40% | 0.00% |
| FICO×LTV | risk-sort | 25.30% | 0.32 | 24.71% | 24.27% | 0.00% |
| CatBoost | risk-sort | 24.73% | 0.15 | 24.47% | 24.23% | 0.00% |

**The correlation took.** Year-to-year variation is now 0.15 to 1.05 points, up
from 0.009 to 0.035 in part 1. Roughly 30x larger. Bad years are now accounted for in our simulation.

**But the ranking is identical to expected return.** CatBoost greedy-return still
leads on every metric, including the two downside metrics. The LP still trails it
by about the same margin as on paper.

**No portfolio ever loses money.** These loans earn about 26 cents of interest per
dollar over 7 years, and a default costs 30 cents. A portfolio only goes negative
if roughly 45% of the loans it holds defaults at one time. Even the worst simulated year does not come
close, because all six portfolios hold low-risk loans.

**Why diversification is not paying off.** A single systematic factor hits every
loan equally, no matter what state it is in. There is no state-level shock in the
model, so spreading across states protects against nothing the simulation can see.
The state cap costs return and buys no measurable downside protection here.

## Impact on the project

- **The constraints cost $21.9M and, under these assumptions, buy nothing
  measurable.** That is an honest result, not a failure. It says the protection
  they offer is invisible to a model with only one shared shock.

- **Next runs test whether this holds.** Asset correlation 0.30 and LGD 50% both
  make bad years worse. If the LP still trails under harsher assumptions, the
  finding is robust rather than an artifact of mild settings.

- **A regional factor would be the honest fix** if we want state diversification
  to matter. That is new scope, so it stays parked until the sensitivity runs are
  done.

## Sensitivity grid: asset correlation x LGD

Six runs: asset correlation 0.0, 0.15, 0.30 crossed with LGD 30% and 50%.

**Why both dials at once.** Correlation and LGD both make bad years worse, and they
may interact. Running one at a time would miss that. Six runs at roughly 15 seconds
each.

**LGD 50% is the downturn case.** Bad years hurt recovery too, so a stressed loss
rate belongs alongside stressed correlation. 30% follows Sirignano and stays the
base case.

**The 0.0 correlation run is also a correctness check.** It should reproduce part
1's near-zero spread.

**Note:** loss scales directly with LGD, so a 50% run uses `loss_if_default x
(0.50 / 0.30)`.

```
rho000_lgd30  done in 13.6s
  rho000_lgd50  done in 13.6s
  rho015_lgd30  done in 13.7s
  rho015_lgd50  done in 13.7s
  rho030_lgd30  done in 13.9s
  rho030_lgd50  done in 13.8s

all 6 runs in 82.3s

Return on dollars funded. All six portfolios, all six runs.

asset correlation 0.00   LGD 30%
  score     rule               avg     std   bad-yr  worst-yrs  yrs w/ loss
  ----------------------------------------------------------------------
  FICOxLTV  risk-sort       25.30%   0.02   25.27%     25.26%        0.00%
  FICOxLTV  greedy-return   30.72%   0.03   30.66%     30.64%        0.00%
  FICOxLTV  LP              30.51%   0.03   30.45%     30.44%        0.00%
  CatBoost  risk-sort       24.73%   0.01   24.72%     24.71%        0.00%
  CatBoost  greedy-return   30.89%   0.02   30.85%     30.83%        0.00%
  CatBoost  LP              30.64%   0.02   30.60%     30.59%        0.00%

asset correlation 0.00   LGD 50%
  score     rule               avg     std   bad-yr  worst-yrs  yrs w/ loss
  ----------------------------------------------------------------------
  FICOxLTV  risk-sort       25.12%   0.03   25.08%     25.07%        0.00%
  FICOxLTV  greedy-return   29.85%   0.06   29.76%     29.73%        0.00%
  FICOxLTV  LP              29.64%   0.06   29.54%     29.52%        0.00%
  CatBoost  risk-sort       24.67%   0.02   24.64%     24.63%        0.00%
  CatBoost  greedy-return   30.39%   0.04   30.32%     30.30%        0.00%
  CatBoost  LP              30.15%   0.04   30.08%     30.07%        0.00%

asset correlation 0.15   LGD 30%
  score     rule               avg     std   bad-yr  worst-yrs  yrs w/ loss
  ----------------------------------------------------------------------
  FICOxLTV  risk-sort       25.30%   0.32   24.71%     24.27%        0.00%
  FICOxLTV  greedy-return   30.72%   1.04   28.67%     27.63%        0.00%
  FICOxLTV  LP              30.51%   1.05   28.46%     27.40%        0.00%
  CatBoost  risk-sort       24.73%   0.15   24.47%     24.23%        0.00%
  CatBoost  greedy-return   30.89%   0.72   29.49%     28.66%        0.00%
  CatBoost  LP              30.65%   0.71   29.26%     28.44%        0.00%

asset correlation 0.15   LGD 50%
  score     rule               avg     std   bad-yr  worst-yrs  yrs w/ loss
  ----------------------------------------------------------------------
  FICOxLTV  risk-sort       25.13%   0.53   24.14%     23.41%        0.00%
  FICOxLTV  greedy-return   29.86%   1.74   26.45%     24.71%        0.00%
  FICOxLTV  LP              29.64%   1.75   26.23%     24.46%        0.00%
  CatBoost  risk-sort       24.67%   0.26   24.23%     23.83%        0.00%
  CatBoost  greedy-return   30.39%   1.20   28.07%     26.68%        0.00%
  CatBoost  LP              30.15%   1.19   27.84%     26.48%        0.00%

asset correlation 0.30   LGD 30%
  score     rule               avg     std   bad-yr  worst-yrs  yrs w/ loss
  ----------------------------------------------------------------------
  FICOxLTV  risk-sort    
... [truncated]
```

## Finding: the ranking holds under every stress we tested

Six runs: asset correlation 0.00 / 0.15 / 0.30 crossed with LGD 30% / 50%.
All values are return on dollars funded.

**The 0.00 correlation run reproduces part 1.** Standard deviations of 0.01 to
0.03, matching part 1's 0.009 to 0.035. The code is correct.

**Both dials work, and they compound.** CatBoost LP standard deviation:

| | LGD 30% | LGD 50% |
|---|---|---|
| correlation 0.00 | 0.02 | 0.04 |
| correlation 0.15 | 0.71 | 1.19 |
| correlation 0.30 | 1.13 | 1.89 |

Correlation multiplies the year-to-year swing by about 50x. LGD adds roughly 65%
on top of that. The harshest run is 95 times more volatile than the calmest.

**Greedy-return beats the LP in all six runs, on every metric.** The gap is
steady: 0.21 to 0.25 points of average return, and a similar gap in bad years. The
constraints cost the same whether conditions are calm or harsh.

**One portfolio lost money, once.** FICO×LTV LP at correlation 0.30 and LGD 50%
returned below zero in 0.01% of years, or 1 year out of 10,000. It is the only
nonzero cell in the grid, and notably it is a constrained portfolio, not greedy.

**Risk-sort has by far the best downside.** In the harshest run, CatBoost
risk-sort still returns 23.18% in its worst years with a standard deviation of
0.47. CatBoost greedy-return drops to 24.02% with a standard deviation of 1.91.
Risk-sort gives up about 6 points of average return to be four times steadier.

## Impact on the project

- **The constraints do not provide downside protection under these assumptions.**
  We tested this two ways and the answer did not move. That is an honest negative
  result, not a failed run.

- **Simple risk-sorting does provide protection.** It is the steadiest portfolio in
  every run, at a large cost in return. Under a much harsher stress it would win
  outright.

- **The state cap cannot pay off in this model, structurally.** A single systematic
  factor hits every loan equally regardless of location. There is no geographic
  risk to diversify against, so spreading across states protects against nothing
  the simulation can see.

- **Next decision:** add a regional factor so geographic diversification has
  something to protect against, or accept this result and write it up as-is.

```
shape: (6, 1)
┌──────────────┐
│ run          │
│ ---          │
│ str          │
╞══════════════╡
│ rho000_lgd30 │
│ rho000_lgd50 │
│ rho015_lgd30 │
│ rho015_lgd50 │
│ rho030_lgd30 │
│ rho030_lgd50 │
└──────────────┘
rows: 60,000   (expect 60,000)
summary rows: 36   (expect 36)
```

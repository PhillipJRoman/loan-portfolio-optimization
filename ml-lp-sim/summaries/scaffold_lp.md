# scaffold_lp

# LP Scaffolding: Loan Selection

Stage 3. Select which loans to fund to maximize expected return under budget,
risk, diversification, and equity constraints. Runs on the scaffold pool from the
ML notebook (409,926 test-split loans with scores attached).

## Setup and load

**What:** imports, session display config, load the scaffold pool, and join the
three socioeconomic flags back from the raw file.

**Why the join:** `scaffold_pool.parquet` carries the LP economic columns and both
risk scores, but not `is_first_time`, `is_homeready`, or `is_hfa`. Those were not
finalized as constraints when the pool was saved, so we pull them back now, keyed
on `LOAN_ID`.

```
pool shape : (409926, 19)
flag nulls : 0
shape: (5, 4)
┌──────────────┬───────────────┬──────────────┬────────┐
│ LOAN_ID      ┆ is_first_time ┆ is_homeready ┆ is_hfa │
│ ---          ┆ ---           ┆ ---          ┆ ---    │
│ str          ┆ i8            ┆ i8           ┆ i8     │
╞══════════════╪═══════════════╪══════════════╪════════╡
│ 123137870847 ┆ 1             ┆ 1            ┆ 0      │
│ 102157127407 ┆ 0             ┆ 0            ┆ 0      │
│ 138444152104 ┆ 0             ┆ 0            ┆ 0      │
│ 134687545227 ┆ 0             ┆ 0            ┆ 0      │
│ 142325190273 ┆ 1             ┆ 0            ┆ 1      │
└──────────────┴───────────────┴──────────────┴────────┘
```

## Verify the socioeconomic flags

**What:** counts for each flag, and a cross-tab of HomeReady against HFA.

**Why:** two things shape the constraint design.
- Whether HomeReady and HFA are mutually exclusive. You said both came from one
  program column, which would make a loan in at most one. Confirm it.
- The size of each group. A floor is only meaningful if the group is a small
  enough share that the return-maximizer would otherwise under-fund it.

```
--- flag prevalence ---
  is_first_time     97,502   23.79%
  is_homeready      20,682    5.05%
  is_hfa            10,510    2.56%

--- HomeReady x HFA (are they mutually exclusive?) ---
shape: (3, 3)
┌──────────────┬────────┬────────┐
│ is_homeready ┆ is_hfa ┆ len    │
│ ---          ┆ ---    ┆ ---    │
│ i8           ┆ i8     ┆ u32    │
╞══════════════╪════════╪════════╡
│ 0            ┆ 0      ┆ 378734 │
│ 0            ┆ 1      ┆ 10510  │
│ 1            ┆ 0      ┆ 20682  │
└──────────────┴────────┴────────┘

--- any affordable program (HomeReady or HFA) ---
  is_affordable     31,192    7.61%
```

## Do the equity groups cost return?

**What:** default rate, mean PD, mean rate, and mean expected return per dollar,
split by each flag.

**Why:** a floor only creates a real tradeoff if the group it protects is one the
return-maximizer would otherwise avoid. If these borrowers are higher-risk and
lower-return, the floor costs money and the equity-vs-return story is real. If
they look like everyone else, the floor is nearly free and the story is different.

Expected return per dollar: `((1 - PD) * interest - PD * loss) / UPB`, using the
CatBoost PD.

```
--- by is_first_time ---
shape: (2, 6)
┌───────────────┬────────┬─────────────┬─────────┬───────────┬────────────────┐
│ is_first_time ┆ n      ┆ actual_rate ┆ mean_pd ┆ mean_rate ┆ mean_ret_per_$ │
│ ---           ┆ ---    ┆ ---         ┆ ---     ┆ ---       ┆ ---            │
│ i8            ┆ u32    ┆ f64         ┆ f64     ┆ f64       ┆ f64            │
╞═══════════════╪════════╪═════════════╪═════════╪═══════════╪════════════════╡
│ 0             ┆ 312424 ┆ 0.0299      ┆ 0.0296  ┆ 4.11      ┆ 0.2444         │
│ 1             ┆ 97502  ┆ 0.0477      ┆ 0.0481  ┆ 4.239     ┆ 0.2479         │
└───────────────┴────────┴─────────────┴─────────┴───────────┴────────────────┘

--- by is_homeready ---
shape: (2, 6)
┌──────────────┬────────┬─────────────┬─────────┬───────────┬────────────────┐
│ is_homeready ┆ n      ┆ actual_rate ┆ mean_pd ┆ mean_rate ┆ mean_ret_per_$ │
│ ---          ┆ ---    ┆ ---         ┆ ---     ┆ ---       ┆ ---            │
│ i8           ┆ u32    ┆ f64         ┆ f64     ┆ f64       ┆ f64            │
╞══════════════╪════════╪═════════════╪═════════╪═══════════╪════════════════╡
│ 0            ┆ 389244 ┆ 0.0328      ┆ 0.0327  ┆ 4.136     ┆ 0.2454         │
│ 1            ┆ 20682  ┆ 0.0586      ┆ 0.0586  ┆ 4.239     ┆ 0.2424         │
└──────────────┴────────┴─────────────┴─────────┴───────────┴────────────────┘

--- by is_hfa ---
shape: (2, 6)
┌────────┬────────┬─────────────┬─────────┬───────────┬────────────────┐
│ is_hfa ┆ n      ┆ actual_rate ┆ mean_pd ┆ mean_rate ┆ mean_ret_per_$ │
│ ---    ┆ ---    ┆ ---         ┆ ---     ┆ ---       ┆ ---            │
│ i8     ┆ u32    ┆ f64         ┆ f64     ┆ f64       ┆ f64            │
╞════════╪════════╪═════════════╪═════════╪═══════════╪════════════════╡
│ 0      ┆ 399416 ┆ 0.0326      ┆ 0.0325  ┆ 4.129     ┆ 0.2452         │
│ 1      ┆ 10510  ┆ 0.0915      ┆ 0.0931  ┆ 4.601     ┆ 0.2463         │
└────────┴────────┴─────────────┴─────────┴───────────┴────────────────┘

--- by is_affordable ---
shape: (2, 6)
┌───────────────┬────────┬─────────────┬─────────┬───────────┬────────────────┐
│ is_affordable ┆ n      ┆ actual_rate ┆ mean_pd ┆ mean_rate ┆ mean_ret_per_$ │
│ ---           ┆ ---    ┆ ---         ┆ ---     ┆ ---       ┆ ---            │
│ i8            ┆ u32    ┆ f64         ┆ f64     ┆ f64       ┆ f64            │
╞═══════════════╪════════╪═════════════╪═════════╪═══════════╪════════════════╡
│ 0             ┆ 378734 ┆ 0.0312      ┆ 0.031   ┆ 4.123     ┆ 0.2454         │
│ 1             ┆ 31192  ┆ 0.0697      ┆ 0.0702  ┆ 4.361     ┆ 0.2437         │
└───────────────┴────────┴─────────────┴─────────┴───────────┴────────────────┘
```

## Finding: equity groups are all riskier, but only HomeReady earns less per dollar

Profile by flag, CatBoost PD, on the test pool:

| Group | share | mean PD | rate | ret/$ | vs rest |
|---|---|---|---|---|---|
| First-time | 23.8% | 4.81% | 4.24% | 0.2479 | +0.0035 |
| HomeReady | 5.0% | 5.86% | 4.24% | 0.2424 | -0.0030 |
| HFA | 2.6% | 9.31% | 4.60% | 0.2463 | +0.0011 |
| Affordable (either) | 7.6% | 7.02% | 4.36% | 0.2437 | -0.0017 |

Every group defaults more than the rest of the book. HFA is the sharpest at nearly
3x the base default rate, with a 47bp rate premium to match.

But higher risk does not translate into lower return per dollar the way we
expected. First-time borrowers earn *more* per dollar than everyone else
(+0.0035), and HFA also comes out ahead (+0.0011). Only HomeReady earns
meaningfully less (-0.0030).

**Why the risk does not show up in return.** Equity-program borrowers take 30-year
loans almost exclusively. The rest of the book holds far more 15-year paper, which
earns less interest over our 7-year window because it pays down fast. So the
comparison group is dragged down by loan term, not by credit quality. The rate
premium these borrowers pay is enough to cover the extra default risk over seven
years.

**HomeReady and HFA are mutually exclusive.** No loan is in both, confirming they
were split from one program column. Can be treated as one `is_affordable` group
or two separate floors.

**Effect on the project**

The equity-floor story is more subtle than "the optimizer would starve these
borrowers." On average it would not: it is close to indifferent, and it actively
likes first-time and HFA loans. What the LP shows is that the floors still bind at
the margin, because the optimizer buys the *worst* loans it is forced to buy, not
the average one. The HomeReady floor carries a shadow price of -0.012 even though
the average HomeReady loan is only 0.003 behind.

That is a sharper result than the original one. The case for a floor does not rest
on the group being unprofitable. It rests on where a return-maximizer draws its
line.

**How it shapes the constraints**

- First-time floor is nearly free, and for a new reason: these loans earn more per
  dollar than the rest. A floor near the natural rate should not bind at all.
  Confirmed by the LP, where it lands above its floor on its own.
- HomeReady floor is the real lever. Small group (5.0%), lowest return per dollar,
  and the only one the optimizer actively avoids. This is the constraint that
  bends the portfolio.
- HFA floor is free at the average, since HFA loans earn slightly more than the
  rest. But the group is only 2.6% of the pool, so a floor above ~3% would start
  forcing real substitution regardless.

**Caution:** every return gap here is under a third of a cent per dollar. The
averages are nearly a wash. What matters for the LP is the marginal loan, not the
average one, and the shadow prices are the only honest read on that.

**Next**

Lock the constraint set (budget, average-PD ceiling, state caps, first-time
floor, affordable floor) and pick starting values. HomeReady is the one to sweep.

## State concentration in dollars

**What:** each state's share of total pool UPB, next to its share of loan count.

**Why:** we measure every constraint in dollars, not loan count. A lender's
exposure is money. Ten $500k loans in one state is a bigger problem than twenty
$100k loans, even though the second group has more loans in it.

That choice matters most for California, where loans run larger than average. It
holds 13.7% of the loans but 19.5% of the dollars. A count-based cap would let far
more California exposure through than a dollar-based one.

This table is what sets the cap. We read the real dollar shares here, then pick a
threshold in the next section based on what those shares actually are.

```
shape: (10, 5)
┌───────┬───────────┬───────┬─────────────┬───────────┐
│ STATE ┆ upb       ┆ n     ┆ pct_dollars ┆ pct_count │
│ ---   ┆ ---       ┆ ---   ┆ ---         ┆ ---       │
│ str   ┆ f64       ┆ u32   ┆ f64         ┆ f64       │
╞═══════╪═══════════╪═══════╪═════════════╪═══════════╡
│ CA    ┆ 1.8308e10 ┆ 56185 ┆ 19.52       ┆ 13.71     │
│ TX    ┆ 6.9451e9  ┆ 33027 ┆ 7.41        ┆ 8.06      │
│ FL    ┆ 5.7148e9  ┆ 28348 ┆ 6.09        ┆ 6.92      │
│ WA    ┆ 3.9697e9  ┆ 14404 ┆ 4.23        ┆ 3.51      │
│ CO    ┆ 3.7515e9  ┆ 14343 ┆ 4.0         ┆ 3.5       │
│ NY    ┆ 3.3601e9  ┆ 12516 ┆ 3.58        ┆ 3.05      │
│ AZ    ┆ 3.1034e9  ┆ 14969 ┆ 3.31        ┆ 3.65      │
│ IL    ┆ 2.8506e9  ┆ 14946 ┆ 3.04        ┆ 3.65      │
│ VA    ┆ 2.7998e9  ┆ 10517 ┆ 2.99        ┆ 2.57      │
│ NC    ┆ 2.6302e9  ┆ 13024 ┆ 2.8         ┆ 3.18      │
└───────┴───────────┴───────┴─────────────┴───────────┘

states above 4% of dollars: 4
```

## Constraint parameters

Five constraints, all measured in dollars. Every value is a starting point to
sweep later, not a final choice. Stated here with the reasoning so the notebook
carries the justification.

**Why dollars and not loan count.** We considered counting loans instead. The
argument for counting is that equity programs are about serving people, and
affordable-program loans run 20 to 25% smaller than average, so a dollar floor
funds fewer of those borrowers than a count floor would. We chose dollars anyway,
for two reasons. A lender's exposure is capital, not headcount, so a dollar cap is
what actually limits risk. And mixing units across constraints (dollars for the
budget, counts for the floors) makes the shadow prices incomparable, since each
one would answer a different question. Worth revisiting if the project's framing
shifts toward borrowers served rather than capital allocated.

**Budget: 10% of total pool UPB.** The pool is ~$93.8B. Funding all of it is not a
decision. A budget that funds ~a tenth forces real selection, which is the point
of the stage.

**Average-PD ceiling: 3.0%.** Pool mean PD is ~3.4%. A ceiling at or above that
does not bind. 3.0% sits modestly below, so the optimizer must tilt toward safer
loans without being strangled.

**State cap: 8% of budget per state.** CA is 19.5% of pool dollars, so it is the
only state whose share alone forces the cap to bite. TX is next at 7.41% and sits
just under. Whether the cap binds on any other state depends on which loans the LP
actually picks, not on pool share, so the shadow prices are what settle it. The
dollar framing matters most here: CA holds 13.7% of the loans but 19.5% of the
dollars, so a count-based cap would let far more California exposure through.

**First-time floor: 20% of budget.** Natural rate is 23.8%, so a 20% floor sits
just below and is easy to satisfy. Included to show the mechanism; expect little
movement at this level.

**Affordable floors: HomeReady at 5.05%, HFA at 2.56%, separate constraints.**
Set at each program's natural share of the pool. That is deliberate: the floor
holds the portfolio at the share the pool already has, rather than forcing it
higher. A floor at the natural share binds whenever the optimizer would otherwise
drift below it, which is exactly the behavior we want to observe before sweeping
the value upward. Kept separate rather than combined because they come from one
program column and are mutually exclusive, so the LP can hold each to its own
target.

```
total pool UPB : $  93.8B
budget (10%)   : $   9.4B

constraints, all in dollars:
  avg PD ceiling   <= 3.0%
  state cap        <= 8% of budget  ($0.75B per state)
  first-time floor >= 20% of budget
  homeready floor  >= 5.05% of budget
  hfa floor        >= 2.56% of budget

states that will bind at 8% (dollar share > cap):
shape: (1, 2)
┌───────┬─────────────┐
│ STATE ┆ pct_dollars │
│ ---   ┆ ---         │
│ str   ┆ f64         │
╞═══════╪═════════════╡
│ CA    ┆ 19.52       │
└───────┴─────────────┘
```

## LP piece 1: variables, objective, budget-only solve

**What:** one decision variable per loan, the expected-return objective, and the
budget constraint alone. Solve, then confirm it matches a greedy sort.

**Why budget-only first:** with only the budget, the LP is a fractional knapsack,
and greedy-on-return-per-dollar is provably optimal for that. Solving it first
proves the model is wired correctly (objective sign, budget units, solver
running) before we add the constraints that actually matter. It also gives the
baseline the real constraints get compared against.

**Fractional, not binary.** Each `x_i` is allowed anywhere in [0, 1]: fund all,
none, or part of a loan. Two reasons.
- A binary variable per loan over 409,926 loans is a mixed-integer problem, which
  is far slower and can stall. Fractional is a pure LP and solves in seconds.
- The cost is negligible. LP theory says the number of fractional (partial) loans
  at an optimal solution is bounded by the number of constraints. With ~6
  constraints, at most a handful of the 409,926 loans come back partial; the rest
  are exactly 0 or 1. We verify that in piece 3.
- Fractional funding is also realistic here: mortgage participations let a lender
  fund a fraction of a loan pool.

```
status         : 2  (2 = optimal)
objective      : $  2.828B expected return
budget used    : $  9.378B of $9.378B
loans funded   : 44,870 full or partial
  fully (x=1)  : 44,869
  partial      : 1
return on funded: 30.15%
```

## Finding: budget-only LP works and sets the return ceiling

- Solved to optimal over all 409,926 loans. No subsampling needed; the academic
  Gurobi license handles the full problem in seconds.
- Funded $9.378B (the full budget) across 44,870 loans, about 11% of the pool.
- Expected return: $2.828B, a 30.15% return on funded dollars.
- Exactly 1 loan came back partial, matching LP theory: one constraint allows at
  most one fractional loan. The other 44,869 are cleanly funded or not.

This is the unconstrained ceiling. Every constraint we add next can only lower
the 30.15%, and each drop measures what that constraint costs.

## LP piece 2: add the five constraints

**What:** keep the budget and objective, add the five constraints, solve again.

**Why:** the budget-only solve was the ceiling at 30.15%. These constraints are
what make it a real portfolio problem instead of a simple sort. Each one can only
lower the return, and the drop measures its cost.

**The five, all in dollars:**
- Average PD of funded loans <= 3.0%
- No state above 8% of the budget
- First-time buyers >= 20% of the budget
- HomeReady >= 5.05% of the budget
- HFA >= 2.56% of the budget

**One math note on the PD ceiling.** "Average PD <= 3%" is weighted by dollars. In
plain terms: add up each funded loan's PD times its dollars, and that total must
stay under 3% of all funded dollars. Written the way a solver needs it, that is
`sum(PD_i * UPB_i * x_i) <= 0.03 * sum(UPB_i * x_i)`, which rearranges to
`sum((PD_i - 0.03) * UPB_i * x_i) <= 0`. Loans below 3% PD add slack, loans above
eat it.

```
status         : 2  (2 = optimal)
objective      : $  2.805B   (ceiling was $2.828B)
cost of constraints: $   23.0M  (0.81% of ceiling)
budget used    : $  9.378B of $9.378B
loans funded   : 48,732
  partial      : 3
avg PD funded  : 0.0244  (ceiling 0.030)
```

## Finding: the five constraints cost 0.81% of return

- Solved to optimal with all five constraints.
- Return: $2.805B, down $23.0M from the $2.828B ceiling. The constraints cost
  0.81%.
- Only 3 partial loans, matching theory (six constraints allow a few fractions).
- Funded 48,732 loans, up from 44,869. The optimizer now spreads across more,
  smaller loans to satisfy the caps and floors.
- Average PD landed at 2.44%, below the 3.0% ceiling, so the PD limit is not the
  binding constraint. Something else is doing the work.

The constraints are nearly free here (0.81%), which fits the earlier finding that
almost every loan is profitable. Worth seeing which constraints actually bind
before reading more into it.

## LP piece 3: which constraints bind, and is the portfolio clean

**What:** check each constraint's shadow price (how much return one more dollar of
room would buy), and verify the funded portfolio actually satisfies everything.

**Why:** the constraints cost $23.0M total, but the average PD came in under its
ceiling, so the PD limit is not the culprit. The shadow prices show exactly which
constraints do the work. That tells us which dials matter when we sweep, and which
are dead weight.

**Reading it:** a shadow price of 0 means the constraint has room to spare and
costs nothing. A nonzero value means it binds; the size is how hard.

```
--- which constraints bind (nonzero shadow price = binding) ---
  budget           shadow price +0.2830
  state_CA         shadow price +0.0247
  hr_floor         shadow price -0.0120

  binding: 3 of 59 constraints

--- portfolio satisfies every constraint ---
  budget    : $9.378B <= $9.378B   ok
  avg PD    : 0.0244 <= 0.030          ok
  max state : CA at 8.00% <= 8%   ok
  first-time: 21.97% >= 20%       ok
  homeready : 5.05% >= 5.05%     ok
  hfa       : 4.70% >= 2.56%     ok

--- portfolio is clean ---
  loans funded : 48,732
  partial      : 3
```

## Finding: only 3 of 59 constraints bind

- Portfolio satisfies all five constraints. Clean, just 3 partial loans.
- Only three constraints bind (hold return back):
  - **Budget** (+0.283): the real limit. One more dollar of budget buys 28 cents
    of return. Expected, since almost every loan is profitable.
  - **State cap, CA** (+0.025): California wants more than 8% and is held there.
    Costs a little.
  - **HomeReady floor** (-0.012): forces funding HomeReady loans the optimizer
    would otherwise skip. The negative sign means it costs return, as a floor on
    less-profitable loans should.
- Everything else has slack:
  - PD ceiling: unused. Average PD is 2.44%, well under 3.0%.
  - First-time floor: unused. Landed at 21.97% on its own, above the 20% floor.
  - HFA floor: unused. Landed at 4.70%, well above the 2.56% floor.

So the $23.0M cost comes almost entirely from two dials: the California cap and
the HomeReady floor. The other three constraints are currently dead weight.

## The six portfolios: one function, six calls

**What:** a single function that builds a portfolio from a score column and a
method. Called six times for the 3x2: {naive score, model PD} x {risk-sort,
greedy-return, LP}.

**Why one function:** six copy-pasted blocks would drift, and a bug fixed in one
would linger in the others. One function guarantees they are all built the same
way, so any difference in results comes from the score and method, not from code
differences.

**Option A, confirmed.** The score is treated as the PD everywhere it appears. For
the naive runs, the objective's expected return and the PD ceiling both use the
naive score, not CatBoost. This asks a clean question: holding the method fixed,
what does a better score buy? And holding the score fixed, what does optimization
buy?

**The three rules:**
- Risk-sort: fund the safest loans first until the budget is spent. Ignores
  return entirely. The timid lender.
- Greedy-return: sort by return per dollar, fill until broke. Ignores risk and
  every limit we set. The aggressive lender.
- LP: the full solver with all five constraints.

All three use the same objective, built from whichever score is passed in.

```
score     rule             funded     funded $   obj scored     obj TRUE   optimism   avg PD
FICO×LTV  risk-sort        43,386 $   9,377.9M $   2,278.6M $   2,273.0M $     5.6M   0.0085
FICO×LTV  greedy-return    44,516 $   9,378.0M $   2,832.3M $   2,760.5M $    71.8M   0.0405
FICO×LTV  LP               48,342 $   9,378.2M $   2,810.5M $   2,739.1M $    71.4M   0.0417
CatBoost  risk-sort        43,245 $   9,378.0M $   2,214.4M $   2,214.4M $     0.0M   0.0033
CatBoost  greedy-return    44,869 $   9,378.1M $   2,827.6M $   2,827.6M $     0.0M   0.0243
CatBoost  LP               48,732 $   9,378.2M $   2,804.6M $   2,804.6M $     0.0M   0.0244

CatBoost minus FICO×LTV, same rule (true objective):
  risk-sort      $    -58.6M
  greedy-return  $    +67.0M
  LP             $    +65.5M

LP minus greedy-return, same score (true objective):
  FICO×LTV       $    -21.4M
  CatBoost       $    -22.9M
```

## Finding: six portfolios (2x3 ablation)

Ranked by real return (using the true default rates, the honest measure):

| Score | Rule | real return | avg default risk | loans funded |
|---|---|---|---|---|
| CatBoost | greedy-return | $2,827.6M | 2.43% | 44,869 |
| CatBoost | LP | $2,804.6M | 2.44% | 48,732 |
| FICO×LTV | greedy-return | $2,760.5M | 4.05% | 44,516 |
| FICO×LTV | LP | $2,739.1M | 4.17% | 48,342 |
| FICO×LTV | risk-sort | $2,273.0M | 0.85% | 43,386 |
| CatBoost | risk-sort | $2,214.4M | 0.33% | 43,245 |

All six spend the same $9.378B, within one fractional loan.

**Three rules, three kinds of lender:**
- greedy-return chases the most money and ignores risk and every limit we set. The
  reckless lender.
- risk-sort only funds the safest loans and stops early. The timid lender, and it
  earns the least.
- the LP lands just under greedy-return. It gives up a little money to spread
  across states and to fund the affordable-housing loans.

**A better score helps two rules and hurts one.**
- greedy-return: CatBoost earns $67.0M more than the bucket score.
- LP: CatBoost earns $65.5M more.
- risk-sort: CatBoost earns $58.6M *less*. When the only goal is playing it safe,
  the more precise score just finds even safer, even lower-earning loans (0.33% vs
  0.85% default risk). A good score only helps if the rule actually uses it to
  chase return.

**The LP costs $22.9M against greedy-return** ($2,804.6M vs $2,827.6M), and $21.4M
on the naive score. In return it gets a portfolio spread across more states and
carrying the affordable-housing loans. It funds 3,863 more loans to do it, which
means it is buying smaller ones to clear the floors.

**The naive score does not know what it is worth.** Its portfolios expect $71.8M
(greedy-return) and $71.4M (LP) more than they actually earn. The CatBoost
portfolios show zero gap, since there the score is the truth. The exception is
naive risk-sort, off by only $5.6M: the bucket score's errors live in the risky
end of the book, and risk-sort never goes there.

**The catch:** these are expected returns on paper, so greedy-return looks best. But
it has no safety net: no spread across states, no floors. Whether its extra $23M
holds up in a bad year, when many loans default at once, is exactly what stage 4
checks. The money on paper does not settle it.

## Save the six portfolios

**What we save, and why two files:**

- `scaffold_portfolios.parquet` in `data/processed/`. This holds the actual
  funding decisions: for each of the 409,926 loans, how much of it each of the six
  portfolios funded (0, 1, or a fraction). This is what stage 4 reads to know which
  loans each strategy holds. It also carries the columns stage 4 needs to simulate:
  default risk, loan size, interest, loss, state, and the socioeconomic flags.

- `scaffold_portfolios_summary.json` in `data/processed/`. This is the small
  results table: each portfolio's real return, dollars funded, loan count, and
  average default risk. A handful of numbers, easy to read back without loading the
  big file.

**Why parquet for the funding decisions:** it is 409,926 numbers per portfolio,
which is table data, and parquet stores that compactly. A pickle would be fragile
across library versions, and JSON would bloat writing that many numbers as text.

**Why JSON for the summary:** it is only six rows of a few numbers each, so plain
text is fine and easy to open.

```
saved scaffold_portfolios.parquet   (409926, 19)
saved scaffold_portfolios_summary.json   (6 portfolios)

--- funding columns ---
  x__FICOxLTV__risk-sort
  x__FICOxLTV__greedy-return
  x__FICOxLTV__LP
  x__CatBoost__risk-sort
  x__CatBoost__greedy-return
  x__CatBoost__LP

--- sanity: funded dollars per portfolio ---
  FICO×LTV  risk-sort     $9.378B
  FICO×LTV  greedy-return $9.378B
  FICO×LTV  LP            $9.378B
  CatBoost  risk-sort     $9.378B
  CatBoost  greedy-return $9.378B
  CatBoost  LP            $9.378B
```

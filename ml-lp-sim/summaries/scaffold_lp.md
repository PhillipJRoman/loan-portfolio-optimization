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
│ 0             ┆ 312424 ┆ 0.0299      ┆ 0.0296  ┆ 4.11      ┆ 0.252          │
│ 1             ┆ 97502  ┆ 0.0477      ┆ 0.0478  ┆ 4.239     ┆ 0.2498         │
└───────────────┴────────┴─────────────┴─────────┴───────────┴────────────────┘

--- by is_homeready ---
shape: (2, 6)
┌──────────────┬────────┬─────────────┬─────────┬───────────┬────────────────┐
│ is_homeready ┆ n      ┆ actual_rate ┆ mean_pd ┆ mean_rate ┆ mean_ret_per_$ │
│ ---          ┆ ---    ┆ ---         ┆ ---     ┆ ---       ┆ ---            │
│ i8           ┆ u32    ┆ f64         ┆ f64     ┆ f64       ┆ f64            │
╞══════════════╪════════╪═════════════╪═════════╪═══════════╪════════════════╡
│ 0            ┆ 389244 ┆ 0.0328      ┆ 0.0326  ┆ 4.136     ┆ 0.2519         │
│ 1            ┆ 20682  ┆ 0.0586      ┆ 0.0583  ┆ 4.239     ┆ 0.2439         │
└──────────────┴────────┴─────────────┴─────────┴───────────┴────────────────┘

--- by is_hfa ---
shape: (2, 6)
┌────────┬────────┬─────────────┬─────────┬───────────┬────────────────┐
│ is_hfa ┆ n      ┆ actual_rate ┆ mean_pd ┆ mean_rate ┆ mean_ret_per_$ │
│ ---    ┆ ---    ┆ ---         ┆ ---     ┆ ---       ┆ ---            │
│ i8     ┆ u32    ┆ f64         ┆ f64     ┆ f64       ┆ f64            │
╞════════╪════════╪═════════════╪═════════╪═══════════╪════════════════╡
│ 0      ┆ 399416 ┆ 0.0326      ┆ 0.0323  ┆ 4.129     ┆ 0.2516         │
│ 1      ┆ 10510  ┆ 0.0915      ┆ 0.0941  ┆ 4.601     ┆ 0.2457         │
└────────┴────────┴─────────────┴─────────┴───────────┴────────────────┘

--- by is_affordable ---
shape: (2, 6)
┌───────────────┬────────┬─────────────┬─────────┬───────────┬────────────────┐
│ is_affordable ┆ n      ┆ actual_rate ┆ mean_pd ┆ mean_rate ┆ mean_ret_per_$ │
│ ---           ┆ ---    ┆ ---         ┆ ---     ┆ ---       ┆ ---            │
│ i8            ┆ u32    ┆ f64         ┆ f64     ┆ f64       ┆ f64            │
╞═══════════════╪════════╪═════════════╪═════════╪═══════════╪════════════════╡
│ 0             ┆ 378734 ┆ 0.0312      ┆ 0.0309  ┆ 4.123     ┆ 0.252          │
│ 1             ┆ 31192  ┆ 0.0697      ┆ 0.0704  ┆ 4.361     ┆ 0.2445         │
└───────────────┴────────┴─────────────┴─────────┴───────────┴────────────────┘
```

## Finding: every equity group is riskier and earns less per dollar

Profile by flag, CatBoost PD, on the test pool:

| Group | share | mean PD | rate | ret/$ | vs rest |
|---|---|---|---|---|---|
| First-time | 23.8% | 4.78% | 4.24% | 0.2498 | -0.0022 |
| HomeReady | 5.1% | 5.83% | 4.24% | 0.2439 | -0.0080 |
| HFA | 2.6% | 9.41% | 4.60% | 0.2457 | -0.0059 |
| Affordable (either) | 7.6% | 7.04% | 4.36% | 0.2445 | -0.0075 |

Every group defaults more than the rest of the book and earns less per dollar,
even though each is charged a higher rate. HFA is the sharpest: nearly 3x the
default rate, a 47bp rate premium, and the premium still does not cover the risk.

**HomeReady and HFA are mutually exclusive.** No loan is in both, confirming they
were split from one program column. Can be treated as one `is_affordable` group
or two separate floors.

**Effect on the project**

This is the core justification for equity floors, shown rather than asserted. A
pure return-maximizer underfunds exactly these borrowers, the numbers show it, and
a floor is the policy correction. The LP demonstrates the mechanism behind
mandated affordable-lending programs.

**How it shapes the constraints**

- First-time floor is weak. The group is already 24% of the pool and costs only
  0.0022/$, so a floor near the natural rate barely binds. Include it, but expect
  little movement.
- Affordable floor is the real lever. Only 7.6% of the pool at 0.0075/$, so any
  floor above ~8% forces the optimizer to reach for loans it would avoid. This is
  the constraint that will bend the portfolio and the one worth studying.

**Caution:** the return gaps are small in absolute terms (0.2 to 0.8 cents per
dollar). Since nearly every loan is profitable, how much a floor bends the
portfolio depends on which loans the budget crowds out. Do not over-promise the
effect size until the LP runs.

**Next**

Lock the constraint set (budget, average-PD ceiling, state caps, first-time
floor, affordable floor) and pick starting values. The affordable floor is the
one to sweep.

## State concentration in dollars

**What:** each state's share of total pool UPB, next to its share of loan count.

**Why:** we are measuring all constraints in dollars, so the state cap binds on
dollar share, not loan count. California loans are larger than average, so its
dollar share runs higher than its count share. This tells us which states a 4%
dollar cap actually limits, so the constraint markdown states the real number
rather than the count-based estimate.

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

**Budget: 10% of total pool UPB.** The pool is ~$95B. Funding all of it is not a
decision. A budget that funds ~a tenth forces real selection, which is the point
of the stage.

**Average-PD ceiling: 3.0%.** Pool mean PD is ~3.4%. A ceiling at or above that
does not bind. 3.0% sits modestly below, so the optimizer must tilt toward safer
loans without being strangled.

**State cap: 8% of budget per state, in dollars.** In dollar terms CA is 19.5% of
the pool and TX is 7.4%, so an 8% cap binds on CA and TX and leaves the other 52
free. Measured in dollars because a lender's exposure is money, not loan count,
and CA's loans run larger than average (13.7% of loans, 19.5% of dollars).

**First-time floor: 20% of budget.** Natural rate is 23.8%, so a 20% floor sits
just below and is easy to satisfy. Included to show the mechanism; expect little
movement at this level.

**Affordable floors: HomeReady at 5.05%, HFA at 2.56%, separate constraints.**
Set at each program's natural share of the pool. Kept separate rather than
combined because they come from one program column and are mutually exclusive, so
the LP can hold each to its own target.

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
Set parameter Username
Set parameter LicenseID to value 2801014
Academic license - for non-commercial use only - expires 2027-03-31
status         : 2  (2 = optimal)
objective      : $  2.820B expected return
budget used    : $  9.378B of $9.378B
loans funded   : 45,430 full or partial
  fully (x=1)  : 45,429
  partial      : 1
return on funded: 30.07%
```

## Finding: budget-only LP works and sets the return ceiling

- Solved to optimal over all 409,926 loans. No subsampling needed; the academic
  Gurobi license handles the full problem in seconds.
- Funded $9.378B (the full budget) across 45,430 loans, about 11% of the pool.
- Expected return: $2.820B, a 30.07% return on funded dollars.
- Exactly 1 loan came back partial, matching LP theory: one constraint allows at
  most one fractional loan. The other 45,429 are cleanly funded or not.

This is the unconstrained ceiling. Every constraint we add next can only lower
the 30.07%, and each drop measures what that constraint costs.

## LP piece 2: add the five constraints

**What:** keep the budget and objective, add the five constraints, solve again.

**Why:** the budget-only solve was the ceiling at 30.07%. These constraints are
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
objective      : $  2.798B   (ceiling was $2.820B)
cost of constraints: $   21.9M  (0.78% of ceiling)
budget used    : $  9.378B of $9.378B
loans funded   : 49,349
  partial      : 3
avg PD funded  : 0.0247  (ceiling 0.030)
```

## Finding: the five constraints cost 0.78% of return

- Solved to optimal with all five constraints.
- Return: $2.798B, down $21.9M from the $2.820B ceiling. The constraints cost
  0.78%.
- Only 3 partial loans, matching theory (six constraints allow a few fractions).
- Funded 49,349 loans, up from 45,429. The optimizer now spreads across more,
  smaller loans to satisfy the caps and floors.
- Average PD landed at 2.47%, below the 3.0% ceiling, so the PD limit is not the
  binding constraint. Something else is doing the work.

The constraints are nearly free here (0.78%), which fits the earlier finding that
almost every loan is profitable. Worth seeing which constraints actually bind
before reading more into it.

## LP piece 3: which constraints bind, and is the portfolio clean

**What:** check each constraint's shadow price (how much return one more dollar of
room would buy), and verify the funded portfolio actually satisfies everything.

**Why:** the constraints cost $21.9M total, but the average PD came in under its
ceiling, so the PD limit is not the culprit. The shadow prices show exactly which
constraints do the work. That tells us which dials matter when we sweep, and which
are dead weight.

**Reading it:** a shadow price of 0 means the constraint has room to spare and
costs nothing. A nonzero value means it binds; the size is how hard.

```
--- which constraints bind (nonzero shadow price = binding) ---
  budget           shadow price +0.2830
  state_CA         shadow price +0.0237
  hr_floor         shadow price -0.0122

  binding: 3 of 59 constraints

--- portfolio satisfies every constraint ---
  budget    : $9.378B <= $9.378B   ok
  avg PD    : 0.0247 <= 0.030          ok
  max state : CA at 8.00% <= 8%   ok
  first-time: 21.14% >= 20%       ok
  homeready : 5.05% >= 5.05%     ok
  hfa       : 4.52% >= 2.56%     ok

--- portfolio is clean ---
  loans funded : 49,349
  partial      : 3
```

## Finding: only 3 of 59 constraints bind

- Portfolio satisfies all five constraints. Clean, just 3 partial loans.
- Only three constraints bind (hold return back):
  - **Budget** (+0.283): the real limit. One more dollar of budget buys 28 cents
    of return. Expected, since almost every loan is profitable.
  - **State cap, CA** (+0.024): California wants more than 8% and is held there.
    Costs a little.
  - **HomeReady floor** (-0.012): forces funding HomeReady loans the optimizer
    would otherwise skip. The negative sign means it costs return, as a floor on
    less-profitable loans should.
- Everything else has slack:
  - PD ceiling: unused. Average PD is 2.47%, well under 3.0%.
  - First-time floor: unused. Landed at 21.14% on its own, above the 20% floor.
  - HFA floor: unused. Landed at 4.52%, well above the 2.56% floor.

So the $21.9M cost comes almost entirely from two dials: the California cap and
the HomeReady floor. The other three constraints are currently dead weight.

## The four portfolios: one function, four calls

**What:** a single function that builds a portfolio from a score column and a
method. Called four times for the 2x2: {naive score, model PD} x {greedy, LP}.

**Why one function:** four copy-pasted blocks would drift, and a bug fixed in one
would linger in the others. One function guarantees the four are built the exact
same way, so any difference in results comes from the score and method, not from
code differences.

**Option A, confirmed.** The score is treated as the PD everywhere it appears. For
the naive runs, the objective's expected return and the PD ceiling both use the
naive score, not CatBoost. This asks a clean question: holding the method fixed,
what does a better score buy? And holding the score fixed, what does optimization
buy?

**Greedy vs LP inside the function:**
- Greedy: sort by return per dollar, fill until budget is spent. No other
  constraints. This is what a naive lender actually does.
- LP: the full solver with all five constraints.

Both use the same objective, built from whichever score is passed in.

```
score     rule             funded   obj (scored)     obj (TRUE)   avg PD
FICO×LTV  risk-sort        43,386 $      2.358B $      2.351B   0.0088
FICO×LTV  greedy-return    45,047 $      2.834B $      2.748B   0.0431
FICO×LTV  LP               48,985 $      2.813B $      2.727B   0.0437
CatBoost  risk-sort        43,892 $      2.312B $      2.312B   0.0033
CatBoost  greedy-return    45,429 $      2.820B $      2.820B   0.0249
CatBoost  LP               49,349 $      2.798B $      2.798B   0.0247
```

## Finding: six portfolios (2x3 ablation)

Ranked by real return (using the true default rates, the honest measure):

| Score | Rule | real return | avg default risk |
|---|---|---|---|
| CatBoost | greedy-return | $2.820B | 2.49% |
| FICO×LTV | greedy-return | $2.748B | 4.31% |
| CatBoost | LP | $2.798B | 2.47% |
| FICO×LTV | LP | $2.727B | 4.37% |
| FICO×LTV | risk-sort | $2.351B | 0.88% |
| CatBoost | risk-sort | $2.312B | 0.33% |

**Three rules, three kinds of lender:**
- greedy-return chases the most money and ignores risk and every limit we set. The
  reckless lender.
- risk-sort only funds the safest loans and stops early. The timid lender, and it
  earns the least.
- the LP lands just under greedy-return. It gives up a little money to spread
  across states and to fund the affordable-housing loans.

**A better score helps two rules and hurts one.**
- greedy-return: CatBoost earns $72M more than the bucket score.
- LP: CatBoost earns $71M more.
- risk-sort: CatBoost earns $39M *less*. When the only goal is playing it safe, the
  more precise score just finds even safer, even lower-earning loans (0.33% vs
  0.88% default risk). A good score only helps if the rule actually uses it to
  chase return.

**The LP costs only $22M against greedy-return** ($2.798B vs $2.820B). In return it
gets a portfolio spread across more states and carrying the affordable-housing
loans.

**The catch:** these are expected returns on paper, so greedy-return looks best. But
it has no safety net: no spread across states, no floors. Whether its extra $22M
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

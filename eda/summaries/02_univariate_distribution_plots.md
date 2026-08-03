# 02_univariate_distribution_plots

#

# Univariate Distribution Plots

## Figure 1 - Univariate Distributions & Default Rate by Bin

```
<Figure size 1800x2600 with 10 Axes>
```

**Observations (Figure 1):**
- FICO is the clearest risk signal
    - borrowers below 660 default at 10-12%, while those above 760 drop below 2%. Sharp cliff around 700
- DTI shows a steady climb 
    - default stays flat below 35 then accelerates above 40, hitting 5%+ above 45
- LTV risk is concentrated at the high end 
    - loans above 95 LTV default at 6.3%, nearly 2× the average
- Loan Amount is mostly flat until jumbo-sized loans ($700K+) spike to 9.8%
    - likely reflects geographic concentration in expensive markets
- Interest Rate is strongly monotonic 
    - higher rate loans default more, rising from 1.2% at low rates to 9.8% at the top band, reflecting how lenders price risk

## Figure 2 — Borrower Demographics

```
<Figure size 2200x600 with 5 Axes>
```

**Observations - Figure 2**
- First-time buyers (4.84%) default at 63% above the average
    - less financial cushion and experience
- Solo borrowers (no co-borrower) default at 4.35% vs 2.36% with a partner
    - second income is a meaningful buffer
- HomeReady (5.92%) and HFA (9.22%) loans confirm that assistance program participation is a strong proxy for financial vulnerability

## Figure 3 - Lenders

```
<Figure size 1400x600 with 1 Axes>
```

**Observations (Figure 3)**
- U.S. Bank N.A. stands out at 8.48% 
    - nearly 4x JPMorgan Chase (2.21%) despite similar borrower profiles, suggesting origination quality differences beyond what FICO and DTI capture
- Most large lenders (Wells Fargo, Quicken, JPMorgan) cluster near or below average
- "Other" at 3.01% — the 931K unknown lenders perform close to average

## Figure 4 - State Distribution

```
<Figure size 2000x700 with 1 Axes>
```

**Observations (Figure 4)**

- Florida (5.7%) and New York (5.6%) are the highest risk states with large loan volumes 
    - Significant concentration risk
- Midwest and Mountain West states (ID, SD, WI, UT) are consistently the safest under 2%
- Coastal and southern states dominate the high-risk end, directly informing the LP diversification constraints

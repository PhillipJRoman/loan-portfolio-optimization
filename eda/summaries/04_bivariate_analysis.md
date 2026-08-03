# 04_bivariate_analysis

### Coarse Heatmap for FICO×DTI default-rate

```
<Figure size 900x700 with 2 Axes>
```

```
Default rate % (rows=FICO, cols=DTI):
dti_band    ≤35  35–43  43–50    50+
fico_band                           
760+       0.85   1.70   2.49   2.80
700–760    2.47   4.11   5.58   6.30
660–700    5.41   7.60   9.51  10.20
<660       9.03  11.34  12.46  14.02 

Cell counts:
dti_band      ≤35   35–43   43–50    50+
fico_band                               
760+       540579  291130  177649  11734
700–760    261785  234621  168963  10362
660–700     84052   90130   70347   4166
<660        34795   36368   26845   1419
```

### Fig. 6: Default rate by FICO × DTI (coarse grid)
- Default risk is monotonic in both dimensions: it rises across every DTI band within each FICO row and across every FICO band within each DTI column, with no reversals. 

- The spread from the safest corner (760+ FICO, DTI ≤35: 0.85%) to the riskiest (<660 FICO, DTI 50+: 14.0%) is roughly 16-fold. The two factors interact super-additively  

- In absolute terms the high-DTI penalty grows as FICO weakens (from ~2 points in the 760+ band to ~5 points below 660), so weak credit and high leverage compound rather than simply add. The 50+ DTI column is thinly populated (n≈28K, and just 1,419 in the riskiest cell), so that column's rates are directionally clear but less precisely estimated

## Figure 7: First-time buyer default premium within FICO × DTI cells

```
<Figure size 900x700 with 2 Axes>
```

```
Unadjusted: first-time 4.84% vs repeat 2.97% (gap +1.87 ppts)
Within-cell mean gap (composition-held-fixed): +3.73 ppts

Per-cell gap (ppts, first-time minus repeat):
dti_band    ≤35  35–43  43–50    50+
fico_band                           
760+       0.34   1.00   1.69   2.35
700–760    0.60   1.65   2.73   3.00
660–700    2.62   4.35   5.19   4.54
<660       4.53   6.93   7.20  10.89
```

```
Loan-weighted within-cell gap (cells with n≥500): +1.71 ppts
Range across solid cells: +0.34 to +7.20 ppts
```

### Fig. 7: First-time buyer default premium within FICO × DTI cells
- Each cell shows the first-time-minus-repeat default rate (percentage points) for borrowers sharing the same FICO and DTI band, isolating the effect of first-time status from differences in creditworthiness. 

- The premium is positive in all sixteen cells, so Block 2's overall first-time gap (4.84% vs 2.97%) is not an artifact of first-time buyers carrying weaker fundamentals: it persists after holding FICO and DTI fixed, at a loan-weighted premium of +1.71 percentage points. 

- The premium also scales with risk, from +0.34 points among prime, low-leverage borrowers to +7.20 in well-populated subprime, high-DTI cells, indicating that first-time status amplifies other risk factors rather than adding a constant offset. 

- The 50+ DTI / <660 FICO cell (+10.9) rests on essentially no first-time loans and is not interpreted.

## Figure 8: Default rate by FICO × LTV (coarse grid)

```
<Figure size 900x700 with 2 Axes>
```

```
Default rate % (rows=FICO, cols=LTV):
ltv_band    ≤80  80–90  90–95    95+
fico_band                           
760+       1.14   1.25   1.73   2.45
700–760    3.14   3.50   4.43   5.59
660–700    5.88   7.04   9.48  11.15
<660       9.01  11.11  14.42  16.77 

Cell counts:
ltv_band      ≤80   80–90  90–95     95+
fico_band                               
760+       517926  282183  80562  140421
700–760    286847  184152  60063  144669
660–700    118827   63994  19264   46610
<660        56201   24202   5681   13343
```

### Fig. 8: Default rate by FICO × LTV (coarse grid) 
- Completing the FICO/DTI/LTV risk triangle, this grid shows the same super-additive structure as Fig. 6, default risk is monotonic in both dimensions with no reversals

- The high-LTV penalty widens as credit weakens from +1.3 percentage points for prime borrowers (760+) to +7.8 points for subprime (<660). 

- The spread from the safest corner (760+ FICO, ≤80 LTV: 1.14%) to the riskiest (<660 FICO, 95+ LTV: 16.77%) is roughly 15-fold, and unlike the 50+ DTI column, every cell here is well populated (minimum n≈6K). 

- That FICO amplifies both DTI and LTV risk identically indicates it acts as a broad risk multiplier rather than an additive factor. This is evidence that an additive PD model would understate risk in the worst segments, and that the joint low-FICO/high-LTV segment (not either factor alone) is the natural target for the LP's diversification constraints.

```
<Figure size 900x700 with 2 Axes>
```

```
Unadjusted: assistance 7.02% vs standard 3.12% (gap +3.91 ppts)
Loan-weighted within-cell gap (n≥500): +2.89 ppts
Assistance loans total: 155,803

Per-cell gap (ppts):
dti_band    ≤35  35–43  43–50    50+
fico_band                           
760+       1.00   1.55   2.01   2.24
700–760    2.43   2.68   3.03   3.00
660–700    4.10   4.71   5.62   4.55
<660       6.36   5.46   5.14  12.66
```

### Fig. 9:  Assistance-program default premium within FICO × DTI cells
- Each cell shows the HomeReady/HFA-minus-standard default rate for borrowers sharing a FICO and DTI band, isolating program participation from creditworthiness. Block 2's large raw gap (assistance 7.02% vs standard 3.12%, +3.91 ppts) is only partly composition as roughly a quarter reflects assistance borrowers carrying weaker fundamentals, but the majority survives, at a loan-weighted within-cell premium of +2.89 percentage points. 

- The premium is positive in every populated cell and, as with first-time status, widens as fundamentals weaken (from +1.0 among prime borrowers to +5–6 in well-populated subprime cells). Program participation therefore carries independent risk signal beyond FICO and DTI, rather than being a pure artifact of borrower composition. 

- Two caveats: the <660/50+ cell (+12.7) rests on essentially no assistance loans and is not interpreted; and because assistance programs disproportionately serve first-time buyers, this premium and the first-time premium of Figure 7 partly reflect the same underlying population.

# Block 4 Summary: Bivariate & Interaction Analysis: Summary

Four interaction figures move past the single-variable view of Blocks 2–3. Three findings recur with the same structure: 

- (1) FICO × DTI (Fig 6): risk is monotonic in both factors with no reversals, spanning 0.85% to 14.0%, and the DTI penalty widens as FICO weakens, the factors compound rather than add. 

- (2) FICO × LTV (Fig 8): the same super-additive pattern on well-populated cells throughout, spanning 1.14% to 16.77%, with the high-LTV penalty growing from +1.3 ppts for prime borrowers to +7.8 for subprime. 

- (3) First-time status (Fig 7): a genuine effect, not composition. The premium survives holding FICO/DTI fixed (+1.71 ppts loan-weighted) and scales with risk. (4) Assistance programs (Fig 9): similarly mostly independent signal, with ~74% of the raw HomeReady/HFA gap persisting within matched cells (+2.89 ppts).

The unifying result: weak credit amplifies every other risk factor. DTI, LTV, first-time status, and program participation all hit harder at low FICO than high. This has two direct implications. 

For modeling, an additive/linear PD specification would systematically understate risk in the worst segments, favoring a model that captures interactions natively (e.g. gradient boosting). 

For the LP, the dangerous segment is the joint low-FICO/high-LTV/high-DTI corner, not any single factor, so diversification constraints should target joint segments rather than marginal caps. One caveat carried forward: first-time status and assistance participation overlap substantially, so their premiums are not fully independent.

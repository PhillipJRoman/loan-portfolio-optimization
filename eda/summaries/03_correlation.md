# 03_correlation

# Correlation

## Figure 5

```
<Figure size 2200x900 with 3 Axes>
```

**Observations**

Full Correlation Matrix (left):

- Orig LTV and Combined LTV are 0.98 correlated 
    - Nearly identical, drop Combined LTV from the ML model, keep Orig LTV
- Loan Amount, Monthly Payment, Interest Income (7yr), and Loss if Default form a tight cluster all 0.97-1.00 correlated with each other    
    - All measuring loan size in different ways, keep only Loan Amount for ML
- Interest Rate and Loan Term are 0.61 correlated
    - Moderate overlap but different enough to keep both
- Primary and co-borrower FICO are 0.67 correlated
    - Related but meaningfully independent, both worth keeping
- DTI and both FICO scores are only -0.19 to -0.21 
    - Largely independent signals, all three belong in the model

Feature Correlation with Default Flag (right):

- FICO Score (Primary) is the strongest predictor at -0.146 
    - Higher FICO = lower default
- FICO Score (Co-Borrower) second strongest at -0.124
    - Independent signal worth keeping despite 53% nulls
- Interest Rate (+0.085) and DTI (+0.077) are the strongest positive predictors
- Loan Age, Monthly Payment, Loss if Default, and Loan Amount are all near zero
    - Weak individual predictors

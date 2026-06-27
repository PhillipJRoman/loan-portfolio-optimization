"""
Reduce Fannie Mae Single-Family Loan Performance files (one row per loan-month)
to a one-row-per-loan analytical dataset, using Polars streaming so it runs on a
24GB laptop without loading a full 8GB file into RAM.

Run from the repo root:
    python src/reduce_fannie.py

Input : data/raw/2017Q1.csv ... 2017Q4.csv   (pipe-delimited, no header, 113 cols)
Output: data/processed/fannie_2017_loan_level.parquet  (one row per loan)
"""

import polars as pl
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
QUARTERS = ["2017Q1", "2017Q2", "2017Q3", "2017Q4"]

# --- DEFAULT DEFINITION -----------------------------------------------------
# These two parameters define what counts as a "default". This is a MODELING
# DECISION for the team, not a fixed truth. Change them and re-run.
#   DLQ_DEFAULT_THRESHOLD: months delinquent that counts as default.
#       6 = 180 days past due (D180), the standard convention. Use 3 for D90.
#   CREDIT_EVENT_CODES: Zero Balance Codes that signal a credit-event ending.
#       02 = Third Party Sale, 03 = Short Sale, 09 = Deed-in-Lieu/REO,
#       15 = Non-Performing Note Sale.
DLQ_DEFAULT_THRESHOLD = 6
CREDIT_EVENT_CODES = ["02", "03", "09", "15"]
# ---------------------------------------------------------------------------

# 113 column names in file order (Fannie's names + the 3 FICO cols added 12/2025)
COLS = [
    "POOL_ID", "LOAN_ID", "ACT_PERIOD", "CHANNEL", "SELLER", "SERVICER",
    "MASTER_SERVICER", "ORIG_RATE", "CURR_RATE", "ORIG_UPB", "ISSUANCE_UPB",
    "CURRENT_UPB", "ORIG_TERM", "ORIG_DATE", "FIRST_PAY", "LOAN_AGE",
    "REM_MONTHS", "ADJ_REM_MONTHS", "MATR_DT", "OLTV", "OCLTV",
    "NUM_BO", "DTI", "CSCORE_B", "CSCORE_C", "FIRST_FLAG", "PURPOSE",
    "PROP", "NO_UNITS", "OCC_STAT", "STATE", "MSA", "ZIP", "MI_PCT",
    "PRODUCT", "PPMT_FLG", "IO", "FIRST_PAY_IO", "MNTHS_TO_AMTZ_IO",
    "DLQ_STATUS", "PMT_HISTORY", "MOD_FLAG", "MI_CANCEL_FLAG", "Zero_Bal_Code",
    "ZB_DTE", "LAST_UPB", "RPRCH_DTE", "CURR_SCHD_PRNCPL", "TOT_SCHD_PRNCPL",
    "UNSCHD_PRNCPL_CURR", "LAST_PAID_INSTALLMENT_DATE", "FORECLOSURE_DATE",
    "DISPOSITION_DATE", "FORECLOSURE_COSTS", "PROPERTY_PRESERVATION_AND_REPAIR_COSTS",
    "ASSET_RECOVERY_COSTS", "MISCELLANEOUS_HOLDING_EXPENSES_AND_CREDITS",
    "ASSOCIATED_TAXES_FOR_HOLDING_PROPERTY", "NET_SALES_PROCEEDS",
    "CREDIT_ENHANCEMENT_PROCEEDS", "REPURCHASES_MAKE_WHOLE_PROCEEDS",
    "OTHER_FORECLOSURE_PROCEEDS", "NON_INTEREST_BEARING_UPB", "PRINCIPAL_FORGIVENESS_AMOUNT",
    "ORIGINAL_LIST_START_DATE", "ORIGINAL_LIST_PRICE", "CURRENT_LIST_START_DATE",
    "CURRENT_LIST_PRICE", "ISSUE_SCOREB", "ISSUE_SCOREC", "CURR_SCOREB",
    "CURR_SCOREC", "MI_TYPE", "SERV_IND", "CURRENT_PERIOD_MODIFICATION_LOSS_AMOUNT",
    "CUMULATIVE_MODIFICATION_LOSS_AMOUNT", "CURRENT_PERIOD_CREDIT_EVENT_NET_GAIN_OR_LOSS",
    "CUMULATIVE_CREDIT_EVENT_NET_GAIN_OR_LOSS", "HOMEREADY_PROGRAM_INDICATOR",
    "FORECLOSURE_PRINCIPAL_WRITE_OFF_AMOUNT", "RELOCATION_MORTGAGE_INDICATOR",
    "ZERO_BALANCE_CODE_CHANGE_DATE", "LOAN_HOLDBACK_INDICATOR", "LOAN_HOLDBACK_EFFECTIVE_DATE",
    "DELINQUENT_ACCRUED_INTEREST", "PROPERTY_INSPECTION_WAIVER_INDICATOR",
    "HIGH_BALANCE_LOAN_INDICATOR", "ARM_5_YR_INDICATOR", "ARM_PRODUCT_TYPE",
    "MONTHS_UNTIL_FIRST_PAYMENT_RESET", "MONTHS_BETWEEN_SUBSEQUENT_PAYMENT_RESET",
    "INTEREST_RATE_CHANGE_DATE", "PAYMENT_CHANGE_DATE", "ARM_INDEX",
    "ARM_CAP_STRUCTURE", "INITIAL_INTEREST_RATE_CAP", "PERIODIC_INTEREST_RATE_CAP",
    "LIFETIME_INTEREST_RATE_CAP", "MARGIN", "BALLOON_INDICATOR",
    "PLAN_NUMBER", "FORBEARANCE_INDICATOR", "HIGH_LOAN_TO_VALUE_HLTV_REFINANCE_OPTION_INDICATOR",
    "DEAL_NAME", "RE_PROCS_FLAG", "ADR_TYPE", "ADR_COUNT", "ADR_UPB",
    "PAYMENT_DEFERRAL_MOD_EVENT_FLAG", "INTEREST_BEARING_UPB",
    "ORIG_CLASSIC_FICO", "ISSUE_CLASSIC_FICO", "CURR_CLASSIC_FICO",
]

assert len(COLS) == 113, f"expected 113 column names, got {len(COLS)}"

rename_map = {f"column_{i+1}": name for i, name in enumerate(COLS)}


def reduce_quarter(path: Path, quarter: str) -> pl.DataFrame:
    """Stream one 8GB quarterly file down to one row per loan."""
    lf = (
        pl.scan_csv(
            path,
            separator="|",
            has_header=False,
            infer_schema_length=0,   # read every column as text; avoids inference errors
            null_values=[""],        # empty field between pipes -> null
        )
        .rename(rename_map)
        .with_columns(
            # months-delinquent as a number; "XX"/"X"/blank become null
            pl.col("DLQ_STATUS").cast(pl.Int32, strict=False).alias("DLQ_NUM")
        )
        .group_by("LOAN_ID")
        .agg(
            # keep all other columns at their first reporting period (origination
            # characteristics are constant; this preserves the full feature set)
            pl.exclude(["LOAN_ID", "DLQ_STATUS", "Zero_Bal_Code", "DLQ_NUM"]).first(),
            # worst delinquency the loan ever reached
            pl.col("DLQ_NUM").max().alias("max_dlq_ever"),
            # the terminal zero-balance code, if any
            pl.col("Zero_Bal_Code").drop_nulls().last().alias("zero_bal_code"),
        )
        .with_columns(
            (
                (pl.col("max_dlq_ever") >= DLQ_DEFAULT_THRESHOLD)
                | pl.col("zero_bal_code").is_in(CREDIT_EVENT_CODES)
            ).fill_null(False).cast(pl.Int8).alias("default_flag")
        )
        .with_columns(pl.lit(quarter).alias("orig_quarter"))
    )
    return lf.collect(engine="streaming")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    parts = []
    for q in QUARTERS:
        path = RAW_DIR / f"{q}.csv"
        if not path.exists():
            print(f"SKIP {q}: {path} not found")
            continue
        print(f"Reducing {q} ...")
        df = reduce_quarter(path, q)
        n = df.height
        rate = df["default_flag"].mean()
        print(f"  {q}: {n:,} loans | default rate {rate:.4%}")
        parts.append(df)

    if not parts:
        print("No files processed.")
        return

    full = pl.concat(parts, how="vertical")
    out = OUT_DIR / "fannie_2017_loan_level.parquet"
    full.write_parquet(out)
    print(f"\nWrote {full.height:,} loans x {full.width} cols -> {out}")
    print(f"Overall default rate: {full['default_flag'].mean():.4%}")


if __name__ == "__main__":
    main()

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent


def get_account_positions():
    """Build local account summaries from the configured accounts CSV."""
    accounts_frame = pd.read_csv(BASE_DIR / "accounts.csv")
    accounts = {}

    for _, row in accounts_frame.iterrows():
        account_id = row["account_id"]
        minimum = float(row["min_balance"])
        current_balance = row.get("balance")
        if pd.isna(current_balance):
            current_balance = minimum

        balance = float(current_balance)
        accounts[account_id] = {
            "total_credit": 0.0,
            "total_debit": 0.0,
            "credit": 0.0,
            "debit": 0.0,
            "balance": balance,
            "transactions": 0,
            "net_cash_flow": 0.0
        }

    return accounts
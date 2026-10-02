import pandas as pd
from collections import defaultdict
from allocation import get_account_positions

# --------------------------------------------------
# READ ACCOUNT RULES FROM accounts.csv
# --------------------------------------------------

def get_account_rules():

    df = pd.read_csv("accounts.csv")

    rules = {}

    for _, row in df.iterrows():

        rules[row["account_id"]] = {
            "name": row["account_name"],
            "bank": row["bank"],
            "minimum": float(row["min_balance"])
        }

    return rules


# --------------------------------------------------
# READ UPCOMING OBLIGATIONS
# --------------------------------------------------

def get_obligations():

    df = pd.read_csv("obligations.csv")

    obligations = []

    for _, row in df.iterrows():

        obligations.append({
            "obligation_id": row["obligation_id"],
            "account_id": row["account_id"],
            "type": row["type"],
            "description": row["description"],
            "amount": float(row["amount"]),
            "due_date": row["due_date"]
        })

    return obligations


# --------------------------------------------------
# CALCULATE ACCOUNT BALANCES
# --------------------------------------------------

def calculate_accounts():
    return get_account_positions()


# --------------------------------------------------
# CREATE TRANSFER PLAN
# --------------------------------------------------

def create_transfer_plan(accounts, rules, obligations=None):

    if obligations is None:
        obligations = []

    # ----------------------------------------------
    # Calculate total upcoming obligations
    # for each account
    # ----------------------------------------------

    upcoming_obligations = defaultdict(float)

    for obligation in obligations:

        account_id = obligation["account_id"]
        amount = obligation["amount"]

        upcoming_obligations[account_id] += amount

    surplus_accounts = []
    deficit_accounts = []

    # ----------------------------------------------
    # Analyze each account
    # ----------------------------------------------

    for account_id, data in accounts.items():

        balance = data["balance"]

        # Get minimum balance from accounts.csv
        if account_id in rules:

            minimum = rules[account_id]["minimum"]

        else:

            # Fallback minimum balance
            minimum = 100000

        # Upcoming payments
        future_obligations = upcoming_obligations.get(
            account_id,
            0
        )

        # Total amount that should remain
        required_cash = (
            minimum
            + future_obligations
        )

        # Money available after future requirements
        available_surplus = (
            balance
            - required_cash
        )

        # ------------------------------------------
        # Surplus account
        # ------------------------------------------

        if available_surplus > 0:

            surplus_accounts.append({
                "account_id": account_id,
                "surplus": available_surplus
            })

        # ------------------------------------------
        # Deficit account
        # ------------------------------------------

        else:

            funding_gap = abs(
                available_surplus
            )

            deficit_accounts.append({
                "account_id": account_id,
                "gap": funding_gap
            })

    transfers = []

    # ----------------------------------------------
    # Match surplus accounts with deficit accounts
    # ----------------------------------------------

    for destination in deficit_accounts:

        remaining_gap = destination["gap"]

        for source in surplus_accounts:

            if remaining_gap <= 0:
                break

            available = source["surplus"]

            if available <= 0:
                continue

            transfer_amount = min(
                available,
                remaining_gap
            )

            transfers.append({
                "source": source["account_id"],
                "destination": destination["account_id"],
                "amount": transfer_amount,
                "reason": "Upcoming obligations + minimum balance"
            })

            # Reduce available surplus
            source["surplus"] -= transfer_amount

            # Reduce remaining funding gap
            remaining_gap -= transfer_amount

    return transfers


# --------------------------------------------------
# MAIN PROGRAM
# --------------------------------------------------

def main():

    print("\nUsing local account and obligation CSV files...")

    # Calculate account balances
    accounts = calculate_accounts()

    # Read account rules
    rules = get_account_rules()

    # Read upcoming obligations
    obligations = get_obligations()

    # Create transfer plan
    transfers = create_transfer_plan(
        accounts,
        rules,
        obligations
    )

    print("\n")
    print("=" * 70)
    print("SMARTFUND TRANSFER PLANNER")
    print("=" * 70)

    # ----------------------------------------------
    # Display upcoming obligations
    # ----------------------------------------------

    print("\nUPCOMING OBLIGATIONS")
    print("-" * 70)

    if not obligations:

        print("No upcoming obligations found.")

    else:

        for obligation in obligations:

            print(
                f"{obligation['description']} | "
                f"Account: {obligation['account_id']} | "
                f"Amount: ₹{obligation['amount']:,.2f} | "
                f"Due: {obligation['due_date']}"
            )

    # ----------------------------------------------
    # Display transfer plan
    # ----------------------------------------------

    print("\n")
    print("=" * 70)
    print("RECOMMENDED TRANSFERS")
    print("=" * 70)

    if not transfers:

        print("\nNo transfers required.")

    else:

        for i, transfer in enumerate(
            transfers,
            1
        ):

            print(
                f"\nTransfer {i}"
            )

            print("-" * 40)

            print(
                "SOURCE ACCOUNT :",
                transfer["source"]
            )

            print(
                "DESTINATION    :",
                transfer["destination"]
            )

            print(
                "TRANSFER AMOUNT: ₹{:,.2f}".format(
                    transfer["amount"]
                )
            )

            print(
                "REASON         :",
                transfer["reason"]
            )

    print("\n")
    print("=" * 70)
    print("SMARTFUND ANALYSIS COMPLETE")
    print("=" * 70)


# --------------------------------------------------
# START PROGRAM
# --------------------------------------------------

if __name__ == "__main__":

    main()
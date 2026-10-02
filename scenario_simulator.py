import pandas as pd


# --------------------------------------------------
# READ OBLIGATIONS
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
# SCENARIO DEFINITIONS
# --------------------------------------------------

SCENARIOS = {

    "normal": {
        "name": "Normal",
        "description": "No changes to expected cash requirements.",
        "extra_expense": 0
    },

    "delayed_collection": {
        "name": "Delayed Collection",
        "description": "Expected customer collection is delayed.",
        "extra_expense": 100000
    },

    "unexpected_expense": {
        "name": "Unexpected Expense",
        "description": "An unexpected business expense occurs.",
        "extra_expense": 150000
    },

    "increased_payroll": {
        "name": "Increased Payroll",
        "description": "Payroll requirement increases.",
        "extra_expense": 100000
    },

    "increased_vendor": {
        "name": "Increased Vendor Payment",
        "description": "Vendor payment requirement increases.",
        "extra_expense": 100000
    }
}


# --------------------------------------------------
# RUN SCENARIO
# --------------------------------------------------

def run_scenario(
    scenario_name,
    accounts,
    rules,
    obligations
):

    if scenario_name not in SCENARIOS:

        raise ValueError(
            "Invalid scenario selected."
        )

    scenario = SCENARIOS[
        scenario_name
    ]

    # ----------------------------------------------
    # Calculate normal obligation total
    # ----------------------------------------------

    total_obligations = sum(
        obligation["amount"]
        for obligation in obligations
    )

    # ----------------------------------------------
    # Scenario adjustment
    # ----------------------------------------------

    extra_expense = scenario[
        "extra_expense"
    ]

    scenario_required_cash = (
        total_obligations
        + extra_expense
    )

    # ----------------------------------------------
    # Calculate current total cash
    # ----------------------------------------------

    total_balance = sum(
        data["balance"]
        for data in accounts.values()
    )

    # ----------------------------------------------
    # Calculate minimum required balance
    # ----------------------------------------------

    total_minimum_balance = 0

    for account_id in accounts:

        if account_id in rules:

            total_minimum_balance += (
                rules[account_id]["minimum"]
            )

        else:

            total_minimum_balance += 100000

    # ----------------------------------------------
    # Calculate available cash
    # ----------------------------------------------

    available_cash = (
        total_balance
        - total_minimum_balance
    )

    # ----------------------------------------------
    # Calculate funding gap
    # ----------------------------------------------

    funding_gap = (
        scenario_required_cash
        - available_cash
    )

    if funding_gap < 0:

        funding_gap = 0

    # ----------------------------------------------
    # Return scenario result
    # ----------------------------------------------

    return {
        "scenario": scenario["name"],
        "description": scenario["description"],
        "current_cash": total_balance,
        "minimum_required": total_minimum_balance,
        "normal_obligations": total_obligations,
        "additional_expense": extra_expense,
        "total_required": scenario_required_cash,
        "available_cash": available_cash,
        "funding_gap": funding_gap
    }


# --------------------------------------------------
# TEST PROGRAM
# --------------------------------------------------

if __name__ == "__main__":

    print("\n")
    print("=" * 70)
    print("SMARTFUND SCENARIO SIMULATOR")
    print("=" * 70)

    print("\nAvailable scenarios:")

    for key, scenario in SCENARIOS.items():

        print(
            f"- {key}: {scenario['name']}"
        )

    print("\nScenario simulator module ready.")
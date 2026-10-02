def ask_smartfund(question, smartfund_context):

    question = question.lower().strip()

    accounts = smartfund_context.get("accounts", {})
    rules = smartfund_context.get("rules", {})
    obligations = smartfund_context.get("obligations", [])
    transfers = smartfund_context.get("recommended_transfers", [])

    # -----------------------------
    # ACCOUNT INFORMATION
    # -----------------------------

    if any(word in question for word in [
        "which account needs funding",
        "account needs funding",
        "need funding",
        "funding required",
        "deficit"
    ]):

        results = []

        for account_id, data in accounts.items():

            minimum = rules.get(
                account_id,
                {"minimum": 100000}
            )["minimum"]

            balance = data["balance"]

            if balance < minimum:

                account_name = rules.get(
                    account_id,
                    {"name": account_id}
                )["name"]

                gap = minimum - balance

                results.append(
                    f"{account_name} needs ₹{gap:,.2f} "
                    f"to reach its minimum balance."
                )

        if results:
            return "Accounts requiring funding:\n\n" + "\n".join(results)

        return "No account currently requires funding based on the configured minimum balances."

    # -----------------------------
    # SURPLUS CASH
    # -----------------------------

    if any(word in question for word in [
        "surplus",
        "excess cash",
        "extra cash",
        "cash available"
    ]):

        results = []

        for account_id, data in accounts.items():

            minimum = rules.get(
                account_id,
                {"minimum": 100000}
            )["minimum"]

            balance = data["balance"]
            surplus = balance - minimum

            if surplus > 0:

                account_name = rules.get(
                    account_id,
                    {"name": account_id}
                )["name"]

                results.append(
                    f"{account_name}: ₹{surplus:,.2f} surplus"
                )

        if results:
            return "Accounts with surplus cash:\n\n" + "\n".join(results)

        return "No surplus cash is currently available."

    # -----------------------------
    # BALANCES
    # -----------------------------

    if any(word in question for word in [
        "balance",
        "balances",
        "how much money",
        "cash position"
    ]):

        results = []

        for account_id, data in accounts.items():

            account_name = rules.get(
                account_id,
                {"name": account_id}
            )["name"]

            results.append(
                f"{account_name}: ₹{data['balance']:,.2f}"
            )

        return "Current account balances:\n\n" + "\n".join(results)

    # -----------------------------
    # OBLIGATIONS
    # -----------------------------

    if any(word in question for word in [
        "obligation",
        "obligations",
        "payment",
        "payments",
        "due",
        "upcoming"
    ]):

        if not obligations:
            return "There are no upcoming obligations in SmartFund."

        total = sum(
            item["amount"]
            for item in obligations
        )

        results = []

        for item in obligations:

            account_name = rules.get(
                item["account_id"],
                {"name": item["account_id"]}
            )["name"]

            results.append(
                f"{item['description']} — "
                f"₹{item['amount']:,.2f} "
                f"(Due: {item['due_date']}) — "
                f"{account_name}"
            )

        return (
            f"Upcoming obligations total ₹{total:,.2f}.\n\n"
            + "\n".join(results)
        )

    # -----------------------------
    # TRANSFERS
    # -----------------------------

    if any(word in question for word in [
        "transfer",
        "transfers",
        "fund movement",
        "move money",
        "recommendation"
    ]):

        if not transfers:
            return "No fund transfers are currently recommended."

        results = []

        for transfer in transfers:

            source_name = rules.get(
                transfer["source"],
                {"name": transfer["source"]}
            )["name"]

            destination_name = rules.get(
                transfer["destination"],
                {"name": transfer["destination"]}
            )["name"]

            results.append(
                f"₹{transfer['amount']:,.2f} "
                f"from {source_name} "
                f"→ {destination_name}"
            )

        return (
            "Recommended fund movements:\n\n"
            + "\n".join(results)
        )

    # -----------------------------
    # HELP
    # -----------------------------

    if any(word in question for word in [
        "hello",
        "hi",
        "hey"
    ]):

        return (
            "Hello! I'm SmartFund Assistant. 👋\n\n"
            "You can ask me about:\n"
            "• Account balances\n"
            "• Accounts needing funding\n"
            "• Surplus cash\n"
            "• Upcoming obligations\n"
            "• Recommended transfers"
        )

    # -----------------------------
    # DEFAULT RESPONSE
    # -----------------------------

    return (
        "I can help you with SmartFund data.\n\n"
        "Try asking:\n"
        "• Which account needs funding?\n"
        "• What are the current balances?\n"
        "• Which account has surplus cash?\n"
        "• What obligations are upcoming?\n"
        "• What transfers are recommended?"
    )
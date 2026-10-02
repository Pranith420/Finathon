import os
import re
import secrets

from flask import (
    Flask,
    flash,
    render_template,
    jsonify,
    request,
    session,
    redirect,
    url_for
)
from chatbot import ask_smartfund

from allocation import get_account_positions

from transfer_planner import (
    calculate_accounts,
    create_transfer_plan,
    get_account_rules,
    get_obligations
)

from scenario_simulator import (
    run_scenario,
    SCENARIOS
)
from supabase_client import SUPABASE_CONFIG_ERROR, supabase

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or secrets.token_hex(32)


PROTECTED_ENDPOINTS = {
    "dashboard",
    "accounts_page",
    "obligations_page",
    "transfer_page",
    "transfers",
    "obligations_api",
    "scenarios",
    "scenario_api",
    "insights_page",
    "chat_api",
}


@app.before_request
def require_login():
    if request.endpoint in PROTECTED_ENDPOINTS and not session.get("logged_in"):
        return redirect(url_for("login"))


def _establish_user_session(user):
    session.clear()
    session["logged_in"] = True
    session["user_id"] = str(user.id)
    if user.email:
        session["user_email"] = user.email


def _signup_error_message(error):
    message = str(getattr(error, "message", error)).lower()
    code = str(getattr(error, "code", "")).lower()

    if (
        code == "user_already_exists"
        or "already registered" in message
        or "already exists" in message
    ):
        return "An account with this email may already exist."
    if "invalid email" in message or "email address is invalid" in message:
        return "Please enter a valid email address."
    return "Unable to create account. Please try again."


def _safe_supabase_error_text(value):
    text = str(value or "")
    text = re.sub(r"(?i)\bBearer\s+\S+", "Bearer [REDACTED]", text)
    text = re.sub(
        r"(?i)\b(?:sb_publishable_|sb_secret_)[A-Za-z0-9_-]+",
        "[REDACTED KEY]",
        text
    )
    text = re.sub(
        r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
        "[REDACTED TOKEN]",
        text
    )
    text = re.sub(
        r"(?i)(access_token|refresh_token|password|api[_-]?key)\s*[:=]\s*[^\s,;}]+",
        r"\1=[REDACTED]",
        text
    )
    text = re.sub(
        r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[REDACTED EMAIL]",
        text
    )
    return text[:500]


@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if supabase is None:
            return render_template("login.html", error=SUPABASE_CONFIG_ERROR)

        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception:
            auth_response = None

        user = getattr(auth_response, "user", None)
        auth_session = getattr(auth_response, "session", None)
        if user and auth_session:
            _establish_user_session(user)
            return redirect(url_for("dashboard"))

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not all((full_name, email, password, confirm_password)):
        error = "Please fill in all fields."
    elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        error = "Please enter a valid email address."
    elif password != confirm_password:
        error = "Passwords do not match."
    elif len(password) < 8:
        error = "Password must be at least 8 characters."
    else:
        if supabase is None:
            error = SUPABASE_CONFIG_ERROR
        else:
            try:
                auth_response = supabase.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {"full_name": full_name}
                    }
                })
            except Exception as signup_error:
                status = getattr(signup_error, "status", None)
                code = _safe_supabase_error_text(
                    getattr(signup_error, "code", "")
                )
                message = _safe_supabase_error_text(
                    getattr(signup_error, "message", "") or signup_error
                )
                app.logger.error(
                    "Supabase signup failed: type=%s status=%s code=%s message=%s",
                    type(signup_error).__name__,
                    status if isinstance(status, (int, str)) else "unknown",
                    code or "unknown",
                    message or "No error message returned."
                )
                error = _signup_error_message(signup_error)
            else:
                user = getattr(auth_response, "user", None)
                auth_session = getattr(auth_response, "session", None)
                if not user or not getattr(user, "id", None):
                    error = "An account with this email may already exist."
                elif auth_session:
                    _establish_user_session(user)
                    return redirect(url_for("dashboard"))
                else:
                    flash(
                        "Account created successfully. Please check your email "
                        "to verify your account.",
                        "success"
                    )
                    return redirect(url_for("login"))

    return render_template(
        "signup.html",
        error=error,
        full_name=full_name,
        email=email
    )


@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("login"))
# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    accounts = get_account_positions()

    # Get upcoming obligations
    obligations = get_obligations()

    # Get account rules
    rules = get_account_rules()


    # ------------------------------------------------
    # BASIC CASH CALCULATIONS
    # ------------------------------------------------

    total_money_in = sum(
        data["total_credit"]
        for data in accounts.values()
    )

    total_money_out = sum(
        data["total_debit"]
        for data in accounts.values()
    )

    total_balance = sum(
        data["balance"]
        for data in accounts.values()
    )

    net_cash_flow = (
        total_money_in
        - total_money_out
    )


    # ------------------------------------------------
    # OBLIGATION CALCULATIONS
    # ------------------------------------------------

    total_obligations = sum(
        obligation["amount"]
        for obligation in obligations
    )


    # ------------------------------------------------
    # MINIMUM BALANCE CALCULATION
    # ------------------------------------------------

    total_minimum_balance = 0

    for account_id in accounts:

        if account_id in rules:

            total_minimum_balance += (
                rules[account_id]["minimum"]
            )

        else:

            # Default minimum if account
            # is not present in accounts.csv

            total_minimum_balance += 100000


    # ------------------------------------------------
    # AVAILABLE CASH
    # ------------------------------------------------

    available_cash = (
        total_balance
        - total_minimum_balance
    )


    # ------------------------------------------------
    # FUNDING GAP
    # ------------------------------------------------

    funding_gap = (
        total_obligations
        - available_cash
    )

    if funding_gap < 0:

        funding_gap = 0


    # ------------------------------------------------
    # CREATE TRANSFER PLAN
    # ------------------------------------------------

    transfer_plan = create_transfer_plan(
        accounts,
        rules,
        obligations
    )


    # ------------------------------------------------
    # SEND EVERYTHING TO index.html
    # ------------------------------------------------

    return render_template(

        "index.html",

        transactions_count=sum(
            data["transactions"]
            for data in accounts.values()
        ),

        accounts=accounts,

        obligations=obligations,

        transfer_plan=transfer_plan,

        total_money_in=total_money_in,

        total_money_out=total_money_out,

        total_balance=total_balance,

        net_cash_flow=net_cash_flow,

        total_obligations=total_obligations,

        total_minimum_balance=total_minimum_balance,

        available_cash=available_cash,

        funding_gap=funding_gap
    )

@app.route("/accounts")
def accounts_page():
    accounts = calculate_accounts()
    rules = get_account_rules()

    return render_template(
        "accounts.html",
        accounts=accounts,
        rules=rules
    )
# ==================================================
# OBLIGATIONS PAGE
# ==================================================

@app.route("/obligations")
def obligations_page():
    obligations = get_obligations()

    return render_template(
        "obligations.html",
        obligations=obligations
    )
# ==================================================
# TRANSFER PLANNER PAGE
# ==================================================

@app.route("/transfers")
def transfer_page():
    accounts = calculate_accounts()

    rules = get_account_rules()

    obligations = get_obligations()

    transfer_plan = create_transfer_plan(
        accounts,
        rules,
        obligations
    )

    return render_template(

        "transfers.html",

        transfers=transfer_plan,

        obligations=obligations
    )


# ==================================================
# TRANSFER API
# ==================================================

@app.route("/api/transfers")
def transfers():
    accounts = calculate_accounts()

    rules = get_account_rules()

    obligations = get_obligations()

    transfer_plan = create_transfer_plan(
        accounts,
        rules,
        obligations
    )

    return jsonify(
        transfer_plan
    )


# ==================================================
# OBLIGATIONS API
# ==================================================

@app.route("/api/obligations")
def obligations_api():

    obligations = get_obligations()

    return jsonify(
        obligations
    )


# ==================================================
# SCENARIO SIMULATOR PAGE
# ==================================================

@app.route("/scenarios")
def scenarios():
    accounts = calculate_accounts()

    rules = get_account_rules()

    obligations = get_obligations()


    # Get scenario selected by user
    selected_scenario = request.args.get(
        "scenario",
        "normal"
    )


    # Calculate scenario
    result = run_scenario(
        selected_scenario,
        accounts,
        rules,
        obligations
    )


    return render_template(

        "scenarios.html",

        scenarios=SCENARIOS,

        selected_scenario=selected_scenario,

        result=result
    )


# ==================================================
# SCENARIO API
# ==================================================

@app.route("/api/scenario/<scenario_name>")
def scenario_api(
    scenario_name
):
    accounts = calculate_accounts()

    rules = get_account_rules()

    obligations = get_obligations()


    result = run_scenario(
        scenario_name,
        accounts,
        rules,
        obligations
    )


    return jsonify(
        result
    )
# ==================================================
# AI INSIGHTS PAGE
# ==================================================

@app.route("/insights")
def insights_page():
    accounts = calculate_accounts()
    rules = get_account_rules()
    obligations = get_obligations()

    insights = []

    # Account-level insights
    for account_id, data in accounts.items():

        minimum = rules.get(
            account_id,
            {"minimum": 100000}
        )["minimum"]

        difference = data["balance"] - minimum

        account_name = rules.get(
            account_id,
            {"name": account_id}
        )["name"]

        if difference > 0:
            insights.append({
                "type": "surplus",
                "title": "Surplus Cash Available",
                "message": (
                    f"{account_name} has "
                    f"₹{difference:,.2f} above its minimum "
                    f"balance requirement."
                )
            })

        else:
            insights.append({
                "type": "warning",
                "title": "Funding Required",
                "message": (
                    f"{account_name} is "
                    f"₹{abs(difference):,.2f} below its "
                    f"minimum balance requirement."
                )
            })

    # Obligation insight
    total_obligations = sum(
        obligation["amount"]
        for obligation in obligations
    )

    if total_obligations > 0:
        insights.append({
            "type": "obligation",
            "title": "Upcoming Cash Requirement",
            "message": (
                f"SmartFund is tracking "
                f"₹{total_obligations:,.2f} "
                f"in upcoming obligations."
            )
        })

    # Transfer insight
    transfer_plan = create_transfer_plan(
        accounts,
        rules,
        obligations
    )

    if transfer_plan:
        total_transfer = sum(
            transfer["amount"]
            for transfer in transfer_plan
        )

        insights.append({
            "type": "transfer",
            "title": "Fund Movement Recommended",
            "message": (
                f"SmartFund recommends "
                f"{len(transfer_plan)} transfer(s) "
                f"totalling ₹{total_transfer:,.2f}."
            )
        })

    else:
        insights.append({
            "type": "success",
            "title": "No Immediate Transfer Required",
            "message": (
                "Current account balances are sufficient "
                "for the planned requirements."
            )
        })

    return render_template(
        "insights.html",
        insights=insights
    )
# ==================================================
# SMARTFUND CHATBOT API
# ==================================================

@app.route("/api/chat", methods=["POST"])
def chat_api():

    data = request.get_json()

    question = data.get("question", "").strip()

    if not question:
        return jsonify({
            "answer": "Please enter a question."
        })

    accounts = calculate_accounts()
    rules = get_account_rules()
    obligations = get_obligations()

    transfer_plan = create_transfer_plan(
        accounts,
        rules,
        obligations
    )

    smartfund_context = {
        "accounts": accounts,
        "rules": rules,
        "obligations": obligations,
        "recommended_transfers": transfer_plan
    }

    answer = ask_smartfund(
        question,
        smartfund_context
    )

    return jsonify({
        "answer": answer
    })

# ==================================================
# START FLASK
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
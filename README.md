# SmartFund

A fintech application for intelligent inter-bank cash allocation and fund movement planning.

## Project Overview

SmartFund analyzes locally configured account minimums and upcoming obligations. It estimates funding gaps, recommends transfers between accounts, and supports scenario planning. Recommendations are planning guidance; the application does not execute bank transfers.

## Features

- Bank account analysis using local account configuration
- Minimum balance management using `accounts.csv`
- Upcoming obligation tracking using `obligations.csv`
- Funding gap calculation
- Surplus cash detection
- Recommended fund movements and transfer planning
- Cash-flow scenario simulation
- Dashboard with account and obligation summaries
- SmartFund Assistant for questions about balances, obligations, and recommendations
- Account signup and session-based login

## Technology Stack

- Python and Flask
- pandas for CSV-backed account rules and obligations
- python-dotenv for local environment configuration
- HTML, CSS, and JavaScript templates

## Project Structure

```text
SmartFund/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── allocation.py
├── app.py
├── chatbot.py
├── scenario_simulator.py
├── transfer_planner.py
├── accounts.csv
├── obligations.csv
└── templates/
    ├── accounts.html
    ├── index.html
    ├── insights.html
    ├── landing.html
    ├── login.html
    ├── obligations.html
    ├── scenarios.html
    ├── signup.html
    └── transfers.html
```

## How It Works

1. Account positions and minimums are loaded from `accounts.csv`; when no `balance` column is present, the configured minimum is used as the local/demo baseline.
2. Upcoming obligations are loaded from `obligations.csv`.
3. The planner compares local account positions with minimums and obligations to identify funding gaps and recommend fund movements.
4. The dashboard, insights, transfer planner, and scenario simulator present those local calculations.

## Installation

Requires Python 3.10 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit your local `.env` with your own credentials. Never replace `.env.example` placeholders with real values.

## Environment Variables

- `FLASK_SECRET_KEY`: long, random secret used to sign Flask sessions. If omitted, a temporary random key is generated for that process; set a persistent value for normal use.
- `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`: server-side Supabase Auth configuration for signup and user login. Use a publishable/anon key; service-role and secret keys are rejected.

There are no built-in demo login credentials. Signup and login use Supabase Auth and require `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` in `.env`.

## How to Run

```powershell
python app.py
```

Open `http://127.0.0.1:5000/` for the landing page. After configuring Supabase Auth and creating an account, sign in to open the dashboard.

This is for local development only. Flask debug mode is enabled; use a production server configuration before deployment.

## Future Improvements

- Add automated tests for allocation, transfers, and scenario calculations.
- Add persistent user and account configuration storage.
- Use Supabase Postgres for account and obligation configuration.
- Add production deployment configuration and operational monitoring.
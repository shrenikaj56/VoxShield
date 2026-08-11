# VoxShield

VoxShield is a software-only hackathon prototype that simulates end-to-end protection for UPI-style payment transactions by combining transaction context, simulated behavioral signals, and voice/scam analysis into one explainable risk decision.

## Project Overview

The product demonstrates how a payment can be analyzed before authorization and intercepted when a combination of payment anomalies, voice-led scam indicators, and user-behavior anomalies cross a configurable protection threshold.

This repository intentionally avoids real banking/UPI integration. It is a synthetic prototype operating on simulated transactional data and simulated fraud patterns.

## Problem

UPI and voice-cloning fraud attacks are increasingly difficult to identify because fraudsters can combine social engineering and suspicious payment instructions before account compromise or before payment authorization is finalized.

## Solution

VoxShield calculates a transaction risk score from:

- transaction signals such as amount, payee familiarity, transaction time, and device/location context,
- behavioral signals from a simulated frontend interaction layer,
- voice/scam indicators from uploaded audio transcripts or rule-based fallback analysis.

Then the product fuses those scores and outputs a decision:

- LOW → allow
- MEDIUM → warn + verify
- HIGH → block + evidence report

## Architecture

The MVP uses a Streamlit dashboard, a SQLite database, modular Python risk modules, and generated HTML evidence reports.

## Features

- Synthetic transaction and fraud-risk analysis
- Voice/scam transcript analysis with deterministic rule-driven fallback
- Simulated behavioral risk signals
- Weighted risk fusion engine with explainable contributors
- Demo scenarios for SAFE, SUSPICIOUS, and HIGH-RISK scam cases
- Risk dashboard with charts and risk indicators
- HTML evidence report generator

## Tech Stack

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- ReportLab
- SQLite
- scikit-learn/XGBoost-ready interface

## Project Structure

```text
VoxShield/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── data/
│   └── synthetic_transactions.csv
├── modules/
│   ├── risk_engine.py
│   ├── transaction_analysis.py
│   ├── voice_analysis.py
│   ├── behavior_analysis.py
│   ├── explainability.py
│   ├── report_generator.py
│   └── database.py
├── pages/
│   ├── payment.py
│   ├── voice.py
│   ├── dashboard.py
│   └── report.py
├── utils/
│   ├── config.py
│   └── helpers.py
└── reports/
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Create a local environment file based on `.env.example`:

```bash
copy .env.example .env
```

Add a Gemini API key only if you have one:

```text
GEMINI_API_KEY=<optional>
```

The app runs without a key using rule-based analysis and transcript fallback.

## How to Run

```bash
streamlit run app.py
```

## Demo Scenarios

The app contains three ready-to-use scenarios:

1. SAFE — amount INR 500, known beneficiary, known device, normal timing.
2. SUSPICIOUS — amount INR 15000, new beneficiary, unusual timing, some behavior anomaly.
3. HIGH-RISK SCAM — amount INR 35000, unknown device, new beneficiary, suspicious voice transcript, scam language.

Use the scenario selector from the Streamlit UI to load a demo profile.

## Limitations

VoxShield is a prototype, not a production-grade bank or UPI fraud system. The model is deterministic and synthetic. Voice analysis uses transcript heuristics and optional API integration when configured.

## Future Scope

- Replace synthetic scoring with supervised training on bank-safe datasets
- API-connected fraud screening and transaction blocking interface
- More robust audio-to-transcript pipelines
- Real user authentication and compliance workflow

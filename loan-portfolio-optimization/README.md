# Loan Portfolio Optimization

Data Science Capstone Project. Team: FinTech Optimizers (Ashay Patla, Ryan Quinlan, Phillip Roman).

## Goal
Given a pool of loan applicants, decide which loans to fund to maximize return under budget and risk constraints. End-to-end pipeline: EDA, ML (default probability), Linear Programming (portfolio selection), Monte Carlo simulation, and a dashboard.

## Structure
- data/raw/ : source data files (gitignored, not committed)
- data/processed/ : reduced shared working dataset
- notebooks/ : exploration and EDA
- src/ : reusable code

## Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

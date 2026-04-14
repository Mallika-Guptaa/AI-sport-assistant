# AI Sports Assistant - Project 1

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Notebook-Jupyter-orange.svg)](https://jupyter.org/)
[![Scikit-learn](https://img.shields.io/badge/ML-scikit--learn-f7931e.svg)](https://scikit-learn.org/)
[![Status](https://img.shields.io/badge/Status-Runnable-success.svg)](#quick-start)

A GitHub-ready AI project that reminds users about upcoming matches, scores match importance, supports natural-language queries, and adds predictive insights.

## Project Story
Sports reminder apps usually stop at calendar alerts: they tell you *when* a game happens, but not *why it matters*.  
This project turns match reminders into an AI-assisted fan experience:
- It identifies high-stakes games (derbies, knockout fixtures, top-4 pressure).
- It adds contextual intelligence (form streaks, momentum, must-win framing).
- It supports natural-language interaction for quick answers.
- It includes predictive insights with explainable reasoning.

The initial version is intentionally designed as a strong internship portfolio piece:
- Clean modular Python architecture
- End-to-end runnable notebooks
- Practical ML baseline with human-readable explanations

## Features
- Upcoming match reminders (1 day and 1 hour before)
- Match info: opponent, competition, kickoff time
- AI-style importance scoring (`low`, `medium`, `high`)
- Context-aware insights (form streak, must-win signals)
- Natural language queries (e.g., "When is Milan's next match?")
- Match outcome prediction + explanation of prediction drivers

## Project Structure
- `src/data_ingestion.py`: fixture + recent-form sample ingestion
- `src/importance_engine.py`: match importance scoring
- `src/reminder_scheduler.py`: reminder generation logic
- `src/nl_interface.py`: natural language query helper
- `src/prediction_engine.py`: simple ML prediction + explanations
- `notebooks/`: runnable notebooks for each component

## Demo Flow
1. Load fixtures + recent form.
2. Score match importance and generate context-aware insights.
3. Build personalized reminders (1 day and 1 hour before).
4. Ask natural-language questions like:
   - "When is Milan's next match?"
   - "Remind me only for big matches"
5. Predict win probability and explain the model decision.

## Quick Start
1. Create environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Launch Jupyter:
   ```bash
   jupyter notebook
   ```
3. Run notebooks in order:
   - `notebooks/01_data_pipeline.ipynb`
   - `notebooks/02_importance_scoring.ipynb`
   - `notebooks/03_reminder_simulation.ipynb`
   - `notebooks/04_nl_queries.ipynb`
   - `notebooks/05_match_prediction.ipynb`
   - `notebooks/06_explain_predictions.ipynb`

## Internship-Relevant Skills Demonstrated
- Data ingestion and feature engineering
- Rule-based + ML hybrid decision systems
- NLP-style query handling
- Model training, evaluation, and explainability
- Production-minded project structure for GitHub

## Next Version Ideas
- Replace sample fixtures with live sports API integration
- Add Telegram/Discord/Email notification delivery
- Add player-level performance modeling with richer features
- Build a lightweight web UI for user preferences and chat

## Notes
- This first version uses simulated fixture/form data for reliability and easy local execution.
- You can later swap in a live sports API in `src/data_ingestion.py`.

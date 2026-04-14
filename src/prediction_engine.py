from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


FEATURES = [
    "home",
    "team_form_points_last5",
    "opp_form_points_last5",
    "team_xg_last5",
    "opp_xg_last5",
    "is_knockout",
]


@dataclass
class PredictionArtifacts:
    model: LogisticRegression
    accuracy: float
    X_test: pd.DataFrame
    y_test: pd.Series


def generate_synthetic_training_data(n: int = 500, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    df = pd.DataFrame(
        {
            "home": rng.integers(0, 2, n),
            "team_form_points_last5": rng.integers(2, 15, n),
            "opp_form_points_last5": rng.integers(2, 15, n),
            "team_xg_last5": rng.uniform(0.6, 2.3, n),
            "opp_xg_last5": rng.uniform(0.6, 2.3, n),
            "is_knockout": rng.integers(0, 2, n),
        }
    )

    logit = (
        0.45 * df["home"]
        + 0.22 * (df["team_form_points_last5"] - df["opp_form_points_last5"])
        + 1.0 * (df["team_xg_last5"] - df["opp_xg_last5"])
        - 0.2 * df["is_knockout"]
    )
    probs = 1 / (1 + np.exp(-logit))
    df["win"] = (rng.uniform(0, 1, n) < probs).astype(int)
    return df


def train_predictor(df: pd.DataFrame) -> PredictionArtifacts:
    X = df[FEATURES]
    y = df["win"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=7)
    model = LogisticRegression(max_iter=300)
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    return PredictionArtifacts(model=model, accuracy=acc, X_test=X_test, y_test=y_test)


def predict_match_win_probability(model: LogisticRegression, feature_row: dict) -> float:
    X_one = pd.DataFrame([feature_row])[FEATURES]
    return float(model.predict_proba(X_one)[0, 1])


def explain_prediction(model: LogisticRegression, feature_row: dict) -> str:
    coeff = dict(zip(FEATURES, model.coef_[0]))
    contributions = {k: coeff[k] * feature_row[k] for k in FEATURES}
    top = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)[:3]

    fragments = []
    for name, val in top:
        if val >= 0:
            fragments.append(f"{name} supports win chances")
        else:
            fragments.append(f"{name} lowers win chances")

    return "Prediction reasoning: " + " + ".join(fragments)

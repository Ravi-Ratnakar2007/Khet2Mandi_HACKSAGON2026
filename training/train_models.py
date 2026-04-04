import os
import pandas as pd
import numpy as np
import pickle

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_absolute_error


# -----------------------------------------------------
# PATH SETUP (works regardless of where script runs)
# -----------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER = os.path.join(BASE_DIR, "..", "data")
MODEL_FOLDER = os.path.join(BASE_DIR, "..", "models")

os.makedirs(MODEL_FOLDER, exist_ok=True)


# -----------------------------------------------------
# PARSE WEEK STRING
# converts "2023-3-W4" -> datetime
# -----------------------------------------------------

def parse_week(week_str):

    year, month, week = week_str.split("-")

    week_num = int(week.replace("W", ""))

    first_day = pd.to_datetime(f"{year}-{month}-01")

    return first_day + pd.Timedelta(days=(week_num - 1) * 7)


# -----------------------------------------------------
# FEATURE ENGINEERING
# -----------------------------------------------------

def build_features(df):

    df = df.sort_values(["Market", "Week"])

    # Price lag features
    df["price_lag1"] = df.groupby("Market")["Modal Price"].shift(1)
    df["price_lag2"] = df.groupby("Market")["Modal Price"].shift(2)

    df["price_3w_avg"] = (
        df.groupby("Market")["Modal Price"]
        .rolling(3)
        .mean()
        .reset_index(level=0, drop=True)
    )

    df["price_momentum"] = df["price_lag1"] - df["price_lag2"]

    # Arrival features
    df["arrival_lag1"] = df.groupby("Market")["Arrival Quantity"].shift(1)

    df["arrival_3w_avg"] = (
        df.groupby("Market")["Arrival Quantity"]
        .rolling(3)
        .mean()
        .reset_index(level=0, drop=True)
    )

    df["supply_pressure"] = df["arrival_lag1"] / df["arrival_3w_avg"]

    # Volatility
    df["volatility_4w"] = (
        df.groupby("Market")["Modal Price"]
        .rolling(4)
        .std()
        .reset_index(level=0, drop=True)
    )

    df = df.dropna()

    return df


# -----------------------------------------------------
# LOAD DATASET
# -----------------------------------------------------

def load_dataset(commodity):

    path = os.path.join(DATA_FOLDER, commodity, "merged", "dataset.csv")

    df = pd.read_csv(path)

    df["Week"] = df["Week"].apply(parse_week)

    return df


# -----------------------------------------------------
# TRAIN MODEL
# -----------------------------------------------------

def train_model(df, commodity):

    df = build_features(df)

    if len(df) < 60:
        print(f"{commodity} skipped (not enough data)")
        return

    # -----------------------------
    # OneHotEncode markets
    # -----------------------------

    encoder = OneHotEncoder(
        sparse_output=False,
        handle_unknown="ignore"
    )

    market_encoded = encoder.fit_transform(df[["Market"]])

    market_cols = encoder.get_feature_names_out(["Market"])

    market_df = pd.DataFrame(
        market_encoded,
        columns=market_cols,
        index=df.index
    )

    df = pd.concat([df, market_df], axis=1)

    # -----------------------------
    # Feature list
    # -----------------------------

    features = [
        "price_lag1",
        "price_lag2",
        "price_3w_avg",
        "price_momentum",
        "arrival_lag1",
        "arrival_3w_avg",
        "supply_pressure",
        "volatility_4w",
        "avg_temp",
        "weekly_rainfall"
    ] + list(market_cols)

    X = df[features]
    y = df["Modal Price"]

    model = RandomForestRegressor(
        n_estimators=400,
        max_depth=8,
        random_state=42
    )

    tscv = TimeSeriesSplit(n_splits=5)

    mae_scores = []

    for train_idx, test_idx in tscv.split(X):

        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

        model.fit(X_train, y_train)

        preds = model.predict(X_test)

        mae = mean_absolute_error(y_test, preds)

        mae_scores.append(mae)

    print(f"\n{commodity.upper()} Model MAE:", round(np.mean(mae_scores), 2))

    # Train final model
    model.fit(X, y)

    # Save model bundle
    with open(os.path.join(MODEL_FOLDER, f"{commodity}_model.pkl"), "wb") as f:

        pickle.dump(
            {
                "model": model,
                "encoder": encoder,
                "features": features
            },
            f
        )

    print(f"Saved {commodity}_model.pkl")


# -----------------------------------------------------
# MAIN TRAINING PIPELINE
# -----------------------------------------------------

def train_all():

    print("DATA FOLDER:", DATA_FOLDER)

    commodities = [
        c for c in os.listdir(DATA_FOLDER)
        if os.path.isdir(os.path.join(DATA_FOLDER, c))
    ]

    print("Commodities detected:", commodities)

    for commodity in commodities:

        try:

            print("\nTraining:", commodity)

            df = load_dataset(commodity)

            train_model(df, commodity)

        except Exception as e:

            print("Error training", commodity, e)


# -----------------------------------------------------

if __name__ == "__main__":
    train_all()
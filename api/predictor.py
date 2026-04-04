import os
import pickle
import pandas as pd
from datetime import timedelta

from .utils import build_prediction_features


# ---------------------------------------------------
# PATHS
# ---------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER = os.path.join(BASE_DIR, "..", "data")
MODEL_FOLDER = os.path.join(BASE_DIR, "..", "models")


# ---------------------------------------------------
# PARSE WEEK STRING
# converts "2026-9-W4" -> datetime
# ---------------------------------------------------

def parse_week(week_str):

    year, month, week = week_str.split("-")

    week_num = int(week.replace("W", ""))

    first_day = pd.to_datetime(f"{year}-{month}-01")

    return first_day + pd.Timedelta(days=(week_num - 1) * 7)


# ---------------------------------------------------
# LOAD MODEL
# ---------------------------------------------------

def load_model(commodity):

    model_path = os.path.join(MODEL_FOLDER, f"{commodity}_model.pkl")

    if not os.path.exists(model_path):
        raise ValueError(f"Model not found for commodity: {commodity}")

    with open(model_path, "rb") as f:
        bundle = pickle.load(f)

    return bundle


# ---------------------------------------------------
# LOAD DATASET
# ---------------------------------------------------

def load_dataset(commodity):

    dataset_path = os.path.join(
        DATA_FOLDER,
        commodity,
        "merged",
        "dataset.csv"
    )

    if not os.path.exists(dataset_path):
        raise ValueError(f"Dataset not found for commodity: {commodity}")

    df = pd.read_csv(dataset_path)

    df["Week"] = df["Week"].apply(parse_week)

    return df


# ---------------------------------------------------
# RESOLVE MARKET NAME
# Case-insensitive lookup — returns the exact name
# as it appears in the dataset, or raises ValueError
# ---------------------------------------------------

def resolve_market(df, market):
    """
    Find the real market name in the dataframe regardless of casing.
    e.g. "karnal" matches "Karnal APMC" or "KARNAL"
    Returns the exact string stored in the Market column.
    """
    all_markets = df["Market"].dropna().unique()

    # 1. Exact match first
    if market in all_markets:
        return market

    # 2. Case-insensitive exact match
    market_lower = market.strip().lower()
    for m in all_markets:
        if m.strip().lower() == market_lower:
            return m

    # 3. Partial match — market name contains the query or vice versa
    for m in all_markets:
        if market_lower in m.strip().lower() or m.strip().lower() in market_lower:
            return m

    raise ValueError(
        f"Market '{market}' not found. "
        f"Available markets: {sorted(all_markets.tolist())}"
    )


# ---------------------------------------------------
# FORECAST ENGINE
# ---------------------------------------------------

def predict_8_weeks(commodity, market):

    bundle = load_model(commodity)

    model = bundle["model"]
    encoder = bundle["encoder"]
    features = bundle["features"]

    df = load_dataset(commodity)

    # Resolve the real market name from the dataset
    resolved_market = resolve_market(df, market)

    df = build_prediction_features(df)

    df_market = df[df["Market"] == resolved_market].copy()

    if df_market.empty:
        raise ValueError(f"Market '{resolved_market}' has no data after feature engineering")

    history = df_market.copy()

    predictions = []

    for step in range(8):

        last_row = history.iloc[-1:].copy()

        # Ensure Week is datetime
        last_row["Week"] = pd.to_datetime(last_row["Week"])

        # ------------------------------
        # Encode Market
        # ------------------------------

        encoded = encoder.transform(last_row[["Market"]])

        market_cols = encoder.get_feature_names_out(["Market"])

        market_df = pd.DataFrame(
            encoded,
            columns=market_cols,
            index=last_row.index
        )

        last_row = pd.concat([last_row, market_df], axis=1)

        # ------------------------------
        # Remove duplicate columns
        # ------------------------------

        last_row = last_row.loc[:, ~last_row.columns.duplicated()]

        # ------------------------------
        # Align features with training
        # ------------------------------

        X = last_row.reindex(columns=features, fill_value=0)

        pred_price = model.predict(X)[0]

        predictions.append(round(pred_price, 2))

        # ------------------------------
        # Create next row
        # ------------------------------

        next_row = last_row.copy()

        next_row["Modal Price"] = pred_price

        next_row["Week"] = pd.to_datetime(last_row["Week"].values[0]) + timedelta(days=7)

        history = pd.concat([history, next_row], ignore_index=True)

        history = build_prediction_features(history)

    return predictions
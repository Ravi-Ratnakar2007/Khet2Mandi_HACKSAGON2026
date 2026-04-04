import pandas as pd


def build_prediction_features(df):

    df = df.sort_values(["Market", "Week"])

    df["price_lag1"] = df.groupby("Market")["Modal Price"].shift(1)
    df["price_lag2"] = df.groupby("Market")["Modal Price"].shift(2)

    df["price_3w_avg"] = (
        df.groupby("Market")["Modal Price"]
        .rolling(3)
        .mean()
        .reset_index(level=0, drop=True)
    )

    df["price_momentum"] = df["price_lag1"] - df["price_lag2"]

    df["arrival_lag1"] = df.groupby("Market")["Arrival Quantity"].shift(1)

    df["arrival_3w_avg"] = (
        df.groupby("Market")["Arrival Quantity"]
        .rolling(3)
        .mean()
        .reset_index(level=0, drop=True)
    )

    df["supply_pressure"] = df["arrival_lag1"] / df["arrival_3w_avg"]

    df["volatility_4w"] = (
        df.groupby("Market")["Modal Price"]
        .rolling(4)
        .std()
        .reset_index(level=0, drop=True)
    )

    return df
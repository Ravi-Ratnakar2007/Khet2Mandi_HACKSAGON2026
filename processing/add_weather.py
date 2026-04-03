import pandas as pd
from weather_fetcher import fetch_weather_history

coords = pd.read_csv("processing/market_coordinates.csv")


def normalize_market(name):

    name = name.lower()
    name = name.replace("apmc","")
    name = name.replace("market","")
    name = name.replace("mandi","")
    name = name.replace(".","")

    return name.strip()


def get_coords(market):

    market = normalize_market(market)

    for _, row in coords.iterrows():

        if row["Market"] in market:
            return row["lat"], row["lon"]

    return None, None


def add_weather(dataset_path):

    df = pd.read_csv(dataset_path)

    weather_frames = []

    markets = df["Market"].unique()

    print("Downloading weather for", len(markets), "markets")

    for market in markets:

        lat, lon = get_coords(market)

        if lat is None:
            continue

        print("Fetching weather:", market)

        w = fetch_weather_history(lat, lon)

        if w is None:
            continue

        w["Market"] = market

        weather_frames.append(w)

    weather_df = pd.concat(weather_frames)

    weather_df["Week"] = (
        weather_df["date"].dt.year.astype(str)
        + "-"
        + weather_df["date"].dt.month.astype(str)
        + "-W"
        + ((weather_df["date"].dt.day - 1)//7 + 1).astype(str)
    )

    weekly_weather = weather_df.groupby(["Market","Week"]).agg({
        "temp":"mean",
        "rain":"sum"
    }).reset_index()

    weekly_weather.rename(columns={
        "temp":"avg_temp",
        "rain":"weekly_rainfall"
    }, inplace=True)

    final = pd.merge(
        df,
        weekly_weather,
        on=["Market","Week"],
        how="left"
    )

    final.to_csv(dataset_path, index=False)

    print("Weather merged successfully.")
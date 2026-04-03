import os
import json
import pandas as pd


# -----------------------------
# WEEK FROM FILENAME
# -----------------------------

def extract_week(filename):

    name = filename.replace(".json", "")
    parts = name.split("_")

    year = parts[-3]
    month = parts[-2]
    week = parts[-1].replace("week", "")

    return f"{year}-{month}-W{week}"


# -----------------------------
# FIND CURRENT WEEK COLUMN
# -----------------------------

def find_price_column(row):

    for k in row.keys():
        if k.startswith("prices_") and row[k] is not None:
            return k

    return None


def find_arrival_column(row):

    for k in row.keys():
        if k.startswith("arrivals_") and row[k] is not None:
            return k

    return None


# -----------------------------
# PARSE PRICE FILES
# -----------------------------

def parse_price_folder(folder):

    rows = []

    for root, _, files in os.walk(folder):

        for file in files:

            if not file.endswith(".json"):
                continue

            path = os.path.join(root, file)

            with open(path) as f:
                data = json.load(f)

            if "rows" not in data:
                continue

            week = extract_week(file)

            for r in data["rows"]:

                market = r.get("market")

                price_col = find_price_column(r)

                if price_col is None:
                    continue

                price = r.get(price_col)

                if price is None:
                    continue

                rows.append({
                    "Week": week,
                    "Market": market.lower(),
                    "Modal Price": float(price)
                })

    df = pd.DataFrame(rows)

    return df


# -----------------------------
# PARSE ARRIVAL FILES
# -----------------------------

def parse_arrival_folder(folder):

    rows = []

    for root, _, files in os.walk(folder):

        for file in files:

            if not file.endswith(".json"):
                continue

            path = os.path.join(root, file)

            with open(path) as f:
                data = json.load(f)

            if "rows" not in data:
                continue

            week = extract_week(file)

            for r in data["rows"]:

                market = r.get("market")

                arrival_col = find_arrival_column(r)

                if arrival_col is None:
                    continue

                arrival = r.get(arrival_col)

                if arrival is None:
                    continue

                rows.append({
                    "Week": week,
                    "Market": market.lower(),
                    "Arrival Quantity": float(arrival)
                })

    df = pd.DataFrame(rows)

    return df


# -----------------------------
# BUILD FINAL DATASET
# -----------------------------

def build_dataset(commodity):

    price_folder = f"data/{commodity}/price"
    arrival_folder = f"data/{commodity}/arrival"

    print("Parsing prices...")
    price_df = parse_price_folder(price_folder)

    print("Parsing arrivals...")
    arrival_df = parse_arrival_folder(arrival_folder)

    print("Price rows:", len(price_df))
    print("Arrival rows:", len(arrival_df))

    df = pd.merge(
        price_df,
        arrival_df,
        on=["Week", "Market"],
        how="inner"
    )

    df = df.dropna()

    save_dir = f"data/{commodity}/merged"
    os.makedirs(save_dir, exist_ok=True)

    save_path = f"{save_dir}/dataset.csv"

    df.to_csv(save_path, index=False)

    print("Saved dataset:", save_path)

    return df
import requests
import os
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://api.agmarknet.gov.in/v1/price-trend/wholesale-arrivals-weekly"

# -----------------------------
# CONFIG
# -----------------------------
COMMODITIES = {
    "banana": 19,
    "wheat":1,
    "rice":3,
    "maize":4,
    "bajra":28,
    "mustartd":12,
    "sunflower":14,
    "cotton":15,
    "apple":17,
    "potato":24
}

STATES = {
    "haryana": 12,
    "punjab": 28,
    "rajasthan": 29
}

START_YEAR = 2022
END_YEAR = datetime.now().year

MAX_WORKERS = 10   # parallel threads

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://agmarknet.gov.in",
    "Referer": "https://agmarknet.gov.in/",
    "User-Agent": "Mozilla/5.0"
}

# -----------------------------
# SINGLE REQUEST FUNCTION
# -----------------------------

def fetch_week(commodity_name, commodity_code, state_name, state_code, year, month, week):

    save_dir = f"data/{commodity_name}/arrival/{state_name}"
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{commodity_name}_{year}_{month}_week{week}.json"
    filepath = os.path.join(save_dir, filename)

    if os.path.exists(filepath):
        return f"Skipped {filename}"

    params = {
        "report_mode": "MarketwiseAll",
        "commodity": commodity_code,
        "state": state_code,
        "year": year,
        "month": month,
        "week": week,
        "export": "false"
    }

    try:
        r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)

        if r.status_code == 400:
            return f"{year}-{month}-W{week} invalid"

        if r.status_code != 200:
            return f"{year}-{month}-W{week} status {r.status_code}"

        if not r.text.strip():
            return f"{year}-{month}-W{week} empty"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(r.text)

        return f"Saved {filepath}"

    except Exception as e:
        return f"Error {year}-{month}-W{week}: {e}"


# -----------------------------
# MAIN PARALLEL DOWNLOADER
# -----------------------------

def download_arrivals():

    tasks = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        for commodity_name, commodity_code in COMMODITIES.items():

            for state_name, state_code in STATES.items():

                print(f"\nQueueing {commodity_name} - {state_name}")

                for year in range(START_YEAR, END_YEAR + 1):
                    for month in range(1, 13):
                        for week in range(1, 6):

                            tasks.append(
                                executor.submit(
                                    fetch_week,
                                    commodity_name,
                                    commodity_code,
                                    state_name,
                                    state_code,
                                    year,
                                    month,
                                    week
                                )
                            )

        for future in as_completed(tasks):
            print(future.result())


if __name__ == "__main__":

    start = time.time()

    download_arrivals()

    print("\n✅ DONE")
    print("Time:", round(time.time() - start, 2), "seconds")
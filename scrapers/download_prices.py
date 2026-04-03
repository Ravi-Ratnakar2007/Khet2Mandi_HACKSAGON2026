import requests
import os
import time
from datetime import datetime

BASE_URL = "https://api.agmarknet.gov.in/v1/price-trend/wholesale-prices-weekly"

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

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://agmarknet.gov.in",
    "Referer": "https://agmarknet.gov.in/",
    "User-Agent": "Mozilla/5.0"
}


# -----------------------------
# DOWNLOAD FUNCTION
# -----------------------------

def download_prices(commodity_name, commodity_code):

    for state_name, state_code in STATES.items():

        save_dir = f"data/{commodity_name}/price/{state_name}"
        os.makedirs(save_dir, exist_ok=True)

        print(f"\nDownloading {commodity_name} prices for {state_name}")

        for year in range(START_YEAR, END_YEAR + 1):

            for month in range(1, 13):

                for week in range(1, 6):

                    params = {
                        "report_mode": "MarketwiseAll",
                        "commodity": commodity_code,
                        "year": year,
                        "month": month,
                        "week": week,
                        "state": state_code,
                        "export": "false"
                    }

                    try:

                        response = requests.get(
                            BASE_URL,
                            params=params,
                            headers=HEADERS,
                            timeout=30
                        )

                        print(f"{state_name} | {year}-{month}-W{week} | {response.status_code}")

                        if response.status_code != 200:
                            continue

                        if not response.text.strip():
                            continue

                        data = response.json()

                        if not data:
                            continue

                        filename = f"{commodity_name}_{year}_{month}_week{week}.json"

                        filepath = os.path.join(save_dir, filename)

                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(response.text)

                        print("Saved:", filepath)

                        time.sleep(0.4)

                    except Exception as e:

                        print("Request error:", e)
                        time.sleep(1)


# -----------------------------
# MAIN LOOP
# -----------------------------

def main():

    for commodity_name, commodity_code in COMMODITIES.items():

        download_prices(
            commodity_name,
            commodity_code
        )

    print("\n✅ PRICE DOWNLOAD COMPLETE")


if __name__ == "__main__":
    main()  
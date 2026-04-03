import requests
import pandas as pd

def fetch_weather_history(lat, lon):

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2018-01-01",
        "end_date": "2024-12-31",
        "daily": "temperature_2m_mean,precipitation_sum",
        "timezone": "auto"
    }

    r = requests.get(url, params=params, timeout=20)

    data = r.json()

    if "daily" not in data:
        return None

    df = pd.DataFrame({
        "date": data["daily"]["time"],
        "temp": data["daily"]["temperature_2m_mean"],
        "rain": data["daily"]["precipitation_sum"]
    })

    df["date"] = pd.to_datetime(df["date"])

    return df
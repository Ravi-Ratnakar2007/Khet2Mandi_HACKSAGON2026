from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import pandas as pd
import os
import math
import statistics
import re

from .predictor import predict_8_weeks, resolve_market, load_dataset

app = FastAPI(title="Khet2Mandi API", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_DIR, "..", "data")
COORDS_PATH = os.path.join(BASE_DIR, "..", "processing", "market_coordinates.csv")


# ─────────────────────────────────────────────
# HAVERSINE
# ─────────────────────────────────────────────

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────────────────────────────────────
# NORMALIZE MARKET NAME
# ─────────────────────────────────────────────

def normalize_name(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\b(apmc|mandi|market|fv|f&v|cantt|city|subji)\b', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


# ─────────────────────────────────────────────
# LOAD COORDINATES
# ─────────────────────────────────────────────

def load_coords() -> pd.DataFrame:
    if not os.path.exists(COORDS_PATH):
        return pd.DataFrame(columns=["Market", "lat", "lon", "normalized"])
    df = pd.read_csv(COORDS_PATH)
    df["normalized"] = df["Market"].apply(normalize_name)
    return df


def find_coord_for_market(market_name: str, coords_df: pd.DataFrame):
    norm = normalize_name(market_name)
    match = coords_df[coords_df["normalized"] == norm]
    if not match.empty:
        return match.iloc[0]["lat"], match.iloc[0]["lon"]
    for _, row in coords_df.iterrows():
        if row["normalized"] and row["normalized"] in norm:
            return row["lat"], row["lon"]
    return None, None


# ─────────────────────────────────────────────
# MARKET SCORING  (FIXED — relative within batch)
# ─────────────────────────────────────────────

def score_market(forecast: list, all_peaks: list = None) -> dict:
    """
    Scores a market 0-100 using four components:

    1. Price score (50%):
       - RELATIVE when all_peaks provided: position within min-max range of the batch.
         e.g. ₹7487 beats ₹6356 correctly instead of both capping at 100.
       - Absolute fallback (peak/30) when called for a single market.

    2. Stability (20%): inverse of std-dev as % of mean. Low volatility = better.

    3. Trajectory (20%): linear slope across 8 weeks. Rising = better.

    4. Upside (10%): late-3-week avg vs early-3-week avg.

    Price weight raised to 50% so a ₹1000 price gap always dominates
    small differences in stability or slope.
    """
    if not forecast or len(forecast) < 2:
        return {
            "score": 0, "confidence": "low",
            "stability_pct": 0, "slope": 0, "upside_pct": 0,
        }

    peak = max(forecast)
    mean = statistics.mean(forecast)
    std  = statistics.stdev(forecast) if len(forecast) > 1 else 0

    # --- Price score: relative within batch ---
    if all_peaks and len(all_peaks) > 1:
        min_p = min(all_peaks)
        max_p = max(all_peaks)
        price_score = ((peak - min_p) / (max_p - min_p) * 100) if max_p > min_p else 50.0
    else:
        # Fallback: absolute scale. ₹3000 = 100, scales down below.
        price_score = min(100.0, peak / 30.0)

    # --- Stability ---
    stability_pct   = (std / mean * 100) if mean else 100.0
    stability_score = max(0.0, 100.0 - stability_pct * 3)

    # --- Trajectory (linear slope) ---
    n      = len(forecast)
    x_mean = (n - 1) / 2.0
    denom  = sum((i - x_mean) ** 2 for i in range(n)) or 1
    slope  = sum((i - x_mean) * (p - mean) for i, p in enumerate(forecast)) / denom
    slope_score = min(100.0, max(0.0, 50.0 + slope * 0.5))

    # --- Upside ---
    early_avg    = statistics.mean(forecast[:3])
    late_avg     = statistics.mean(forecast[-3:])
    upside       = (late_avg - early_avg) / early_avg * 100 if early_avg else 0.0
    upside_score = min(100.0, max(0.0, 50.0 + upside * 2))

    composite = round(min(100.0, max(0.0, (
        0.50 * price_score
        + 0.20 * stability_score
        + 0.20 * slope_score
        + 0.10 * upside_score
    ))), 1)

    confidence = (
        "high"   if mean and std / mean < 0.05 else
        "medium" if mean and std / mean < 0.12 else
        "low"
    )

    return {
        "score":         composite,
        "confidence":    confidence,
        "stability_pct": round(stability_pct, 2),
        "slope":         round(slope, 4),
        "upside_pct":    round(upside, 2),
    }


# ─────────────────────────────────────────────
# BATCH FORECAST HELPER
# collects forecasts for a list of markets,
# then scores all of them relatively
# ─────────────────────────────────────────────

def batch_forecast_and_score(commodity: str, markets: list) -> list:
    """
    Step 1: collect raw forecasts for every market.
    Step 2: score all markets relative to each other using the batch peak list.
    This guarantees the highest-priced market always ranks first on price.
    """
    raw = []
    for market in markets:
        try:
            forecast = predict_8_weeks(commodity, market)
            if not forecast:
                continue
            raw.append({
                "market":   market,
                "forecast": forecast,
                "peak":     max(forecast),
                "avg":      sum(forecast) / len(forecast),
                "best_week": forecast.index(max(forecast)) + 1,
            })
        except Exception as e:
            print(f"[batch] Skipping {market}: {e}")
            continue

    if not raw:
        return []

    all_peaks = [r["peak"] for r in raw]

    results = []
    for r in raw:
        scoring = score_market(r["forecast"], all_peaks=all_peaks)
        results.append({
            "market":      r["market"],
            "price":       round(r["peak"], 2),
            "mean_price":  round(r["avg"], 2),
            "best_week":   r["best_week"],
            "score":       scoring["score"],
            "confidence":  scoring["confidence"],
            "upside_pct":  scoring["upside_pct"],
            "forecast":    r["forecast"],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Khet2Mandi API v2.1", "status": "ok"}


@app.get("/commodities")
def get_commodities():
    if not os.path.exists(DATA_FOLDER):
        return {"commodities": []}
    commodities = sorted([
        f for f in os.listdir(DATA_FOLDER)
        if os.path.isdir(os.path.join(DATA_FOLDER, f))
        and os.path.exists(os.path.join(DATA_FOLDER, f, "merged", "dataset.csv"))
    ])
    return {"commodities": commodities}


@app.get("/markets")
def get_markets(commodity: str):
    path = os.path.join(DATA_FOLDER, commodity, "merged", "dataset.csv")
    if not os.path.exists(path):
        return {"markets": []}
    df = pd.read_csv(path)
    markets = sorted(df["Market"].dropna().unique().tolist())
    return {"markets": markets}


@app.get("/predict")
def predict(commodity: str, market: str):
    try:
        forecast = predict_8_weeks(commodity, market)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    best_price = max(forecast)
    best_week  = forecast.index(best_price) + 1
    # Single-market call — uses absolute scoring (no batch peers)
    scoring    = score_market(forecast)

    try:
        df       = load_dataset(commodity)
        resolved = resolve_market(df, market)
    except Exception:
        resolved = market

    return {
        "commodity":      commodity,
        "market":         resolved,
        "forecast":       forecast,
        "best_week_to_sell": best_week,
        "expected_price": round(best_price, 2),
        "mean_price":     round(sum(forecast) / len(forecast), 2),
        "score":          scoring["score"],
        "confidence":     scoring["confidence"],
        "meta":           scoring,
    }


@app.get("/best-markets")
def best_markets(
    commodity: str,
    top_n: int = Query(default=5, ge=1, le=20),
    min_confidence: Optional[str] = None,
):
    """
    Sweeps ALL markets, scores relatively within the batch so the
    highest-priced market always wins on price component.
    """
    path = os.path.join(DATA_FOLDER, commodity, "merged", "dataset.csv")
    if not os.path.exists(path):
        return {"markets": [], "total_markets_evaluated": 0}

    df      = pd.read_csv(path)
    markets = sorted(df["Market"].dropna().unique().tolist())

    results = batch_forecast_and_score(commodity, markets)

    if min_confidence:
        conf_rank = {"low": 0, "medium": 1, "high": 2}
        results = [
            r for r in results
            if conf_rank.get(r["confidence"], 0) >= conf_rank.get(min_confidence, 0)
        ]

    return {
        "markets":                 results[:top_n],
        "total_markets_evaluated": len(markets),
    }


@app.get("/nearby-markets")
def nearby_markets(
    commodity: str,
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    top_n: int  = Query(default=8, ge=1, le=20),
    max_km: float = Query(default=500, description="Max radius km"),
):
    """
    1. Filter to markets within max_km of user.
    2. Run batch forecasts for those markets only.
    3. Score relatively within that batch — nearest high-price market wins.
    4. Return sorted by score with distance attached.
    """
    path = os.path.join(DATA_FOLDER, commodity, "merged", "dataset.csv")
    if not os.path.exists(path):
        return {"markets": [], "user_location": {"lat": lat, "lon": lon}}

    df_data    = pd.read_csv(path)
    all_markets = sorted(df_data["Market"].dropna().unique().tolist())
    coords_df  = load_coords()

    # Build distance table
    markets_with_distance = []
    for market in all_markets:
        mlat, mlon = find_coord_for_market(market, coords_df)
        if mlat is None:
            continue
        dist = haversine_km(lat, lon, mlat, mlon)
        if dist <= max_km:
            markets_with_distance.append({
                "market":      market,
                "lat":         mlat,
                "lon":         mlon,
                "distance_km": round(dist, 1),
            })

    markets_with_distance.sort(key=lambda x: x["distance_km"])
    nearest      = markets_with_distance[:top_n]
    nearest_names = [e["market"] for e in nearest]

    # Batch forecast + relative scoring
    scored = batch_forecast_and_score(commodity, nearest_names)

    # Re-attach distance info
    dist_lookup = {e["market"]: e for e in nearest}
    results = []
    for r in scored:
        geo = dist_lookup.get(r["market"], {})
        results.append({
            **r,
            "distance_km": geo.get("distance_km"),
            "lat":         geo.get("lat"),
            "lon":         geo.get("lon"),
        })

    # Already sorted by score from batch_forecast_and_score
    return {
        "markets":                  results,
        "user_location":            {"lat": lat, "lon": lon},
        "total_nearby_found":       len(markets_with_distance),
        "total_markets_in_dataset": len(all_markets),
    }


@app.get("/market-summary")
def market_summary(commodity: str):
    """Fast overview: best market + price range. Caps at 10 markets for speed."""
    path = os.path.join(DATA_FOLDER, commodity, "merged", "dataset.csv")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Dataset not found")

    df      = pd.read_csv(path)
    markets = sorted(df["Market"].dropna().unique().tolist())

    results = batch_forecast_and_score(commodity, markets[:10])
    if not results:
        raise HTTPException(status_code=500, detail="No forecasts generated")

    return {
        "commodity":        commodity,
        "total_markets":    len(markets),
        "best_market":      results[0]["market"],
        "best_market_price": results[0]["price"],
        "avg_peak_price":   round(sum(r["price"] for r in results) / len(results), 2),
        "price_range": {
            "min": round(min(r["price"] for r in results), 2),
            "max": round(max(r["price"] for r in results), 2),
        },
    }
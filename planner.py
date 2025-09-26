import requests
import pandas as pd
from datetime import datetime

# Default setup
CITIES = ["Los Angeles, US", "San Diego, US", "New York, US", "Saint Louis, US", "Austin, US"]
DAYS = 16  # Open-Meteo supports up to 16 days

def geocode_city(city):
    """Get latitude/longitude for a city using Open-Meteo's free geocoding API."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(url, params={"name": city, "count": 1}, timeout=20)
    r.raise_for_status()
    data = r.json()
    if not data.get("results"):
        raise ValueError(f"Could not geocode: {city}")
    best = data["results"][0]
    return best["latitude"], best["longitude"], best["name"]

def fetch_forecast(lat, lon, days):
    """Fetch daily forecast from Open-Meteo API."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "forecast_days": days,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_mean",
            "windspeed_10m_max"
        ],
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "precipitation_unit": "inch",
        "timezone": "auto",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def assess(temp, precip_prob, precip, wind):
    """Decide if the day is suitable for an outdoor meeting."""
    if precip_prob > 30 or precip > 0.08:
        return "No"
    if temp < 60 or temp > 85:
        return "Maybe"
    if wind > 20:
        return "No"
    return "Yes"

def main():
    all_rows = []
    for city in CITIES:
        try:
            lat, lon, resolved = geocode_city(city)
            forecast = fetch_forecast(lat, lon, DAYS)
            for i, date in enumerate(forecast["daily"]["time"]):
                temp = forecast["daily"]["temperature_2m_max"][i]
                precip_prob = forecast["daily"]["precipitation_probability_mean"][i]
                precip = forecast["daily"]["precipitation_sum"][i]
                wind = forecast["daily"]["windspeed_10m_max"][i]
                status = assess(temp, precip_prob, precip, wind)
                all_rows.append({
                    "City": resolved,
                    "Date": date,
                    "TempMaxF": temp,
                    "PrecipProb%": precip_prob,
                    "PrecipIn": precip,
                    "WindMaxMph": wind,
                    "Suitable": status
                })
            print(f"✔ Got forecast for {resolved}")
        except Exception as e:
            print(f"[WARN] {city}: {e}")

    # Save all results to CSV
    df = pd.DataFrame(all_rows)
    out_file = f"forecast_{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
    df.to_csv(out_file, index=False)

    # Print preview
    print(f"\nSaved results → {out_file}\n")
    print(df.head(15).to_string(index=False))

if __name__ == "__main__":
    main()

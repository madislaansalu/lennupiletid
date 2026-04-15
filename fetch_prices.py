import os
import json
import datetime
import requests

API_KEY = os.environ["SERPAPI_KEY"]
ORIGIN = "TLL"
DESTINATIONS = ["NRT", "HND"]  # Tokyo Narita + Haneda
DATES = [f"2027-04-{d:02d}" for d in range(1, 11)]
CABINS = {"BUSINESS": 3, "PREMIUM_ECONOMY": 2}
DATA_FILE = "data/prices.json"

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"updated": "", "entries": []}

def fetch(destination, date, cabin_label, cabin_code):
    params = {
        "engine": "google_flights",
        "departure_id": ORIGIN,
        "arrival_id": destination,
        "outbound_date": date,
        "travel_class": cabin_code,
        "currency": "EUR",
        "hl": "et",
        "api_key": API_KEY
    }
    try:
        r = requests.get("https://serpapi.com/search", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        flights = data.get("best_flights", []) or data.get("other_flights", [])
        if not flights:
            return None
        best = flights[0]
        legs = best.get("flights", [])
        airlines = list({leg.get("airline", "") for leg in legs})
        duration = best.get("total_duration", 0)
        stops = len(legs) - 1
        price = best.get("price")
        if not price:
            return None
        return {
            "price": float(price),
            "airlines": airlines,
            "duration_min": duration,
            "stops": stops
        }
    except Exception as e:
        print(f"Viga {destination} {date} {cabin_label}: {e}")
        return None

def main():
    data = load_existing()
    today = datetime.date.today().isoformat()
    new_entries = []

    for date in DATES:
        for destination in DESTINATIONS:
            for cabin_label, cabin_code in CABINS.items():
                result = fetch(destination, date, cabin_label, cabin_code)
                if result:
                    entry = {
                        "checked": today,
                        "flight_date": date,
                        "destination": destination,
                        "cabin": cabin_label,
                        "best_price": result["price"],
                        "airlines": result["airlines"],
                        "duration_min": result["duration_min"],
                        "stops": result["stops"]
                    }
                    new_entries.append(entry)
                    h, m = divmod(result["duration_min"], 60)
                    print(f"{date} {destination} {cabin_label}: {result['price']} EUR | {h}h{m}m | {result['airlines']}")

    data["updated"] = today
    data["entries"].extend(new_entries)

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSalvestatud {len(new_entries)} kirjet.")

if __name__ == "__main__":
    main()

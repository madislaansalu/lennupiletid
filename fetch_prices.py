import os
import json
import datetime
from amadeus import Client, ResponseError

amadeus = Client(
    client_id=os.environ["AMADEUS_API_KEY"],
    client_secret=os.environ["AMADEUS_API_SECRET"]
)

ORIGIN = "TLL"
DESTINATIONS = ["NRT", "HND"]  # Tokyo Narita + Haneda
DATES = [f"2027-04-{d:02d}" for d in range(1, 11)]  # 1.–10. aprill 2027
CABINS = ["BUSINESS", "PREMIUM_ECONOMY"]

DATA_FILE = "data/prices.json"

def load_existing():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"updated": "", "entries": []}

def fetch_offers(destination, date, cabin):
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=ORIGIN,
            destinationLocationCode=destination,
            departureDate=date,
            adults=1,
            travelClass=cabin,
            currencyCode="EUR",
            max=5
        )
        offers = []
        for offer in response.data:
            price = float(offer["price"]["total"])
            airlines = list({
                seg["carrierCode"]
                for itin in offer["itineraries"]
                for seg in itin["segments"]
            })
            duration = offer["itineraries"][0]["duration"]
            stops = sum(
                len(itin["segments"]) - 1
                for itin in offer["itineraries"]
            )
            offers.append({
                "price": price,
                "airlines": airlines,
                "duration": duration,
                "stops": stops
            })
        return offers
    except ResponseError as e:
        print(f"Viga {destination} {date} {cabin}: {e}")
        return []

def main():
    data = load_existing()
    today = datetime.date.today().isoformat()
    new_entries = []

    for date in DATES:
        for destination in DESTINATIONS:
            for cabin in CABINS:
                offers = fetch_offers(destination, date, cabin)
                if offers:
                    best = min(offers, key=lambda x: x["price"])
                    new_entries.append({
                        "checked": today,
                        "flight_date": date,
                        "destination": destination,
                        "cabin": cabin,
                        "best_price": best["price"],
                        "airlines": best["airlines"],
                        "duration": best["duration"],
                        "stops": best["stops"],
                        "all_offers": offers
                    })
                    print(f"{date} {destination} {cabin}: {best['price']} EUR")

    data["updated"] = today
    data["entries"].extend(new_entries)

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Salvestatud {len(new_entries)} kirjet.")

if __name__ == "__main__":
    main()

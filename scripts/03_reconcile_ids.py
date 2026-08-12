"""
Build ID reconciliation maps between the base Kaggle dataset's integer
surrogate keys and Jolpica-F1's string refs (driverRef/constructorRef/
circuitRef) and status text. New entities not present in the base dataset
get freshly minted sequential IDs, logged for manual review.
"""
import json
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = ROOT / "working" / "base"
RAW_DIR = ROOT / "working" / "raw_jolpica"
OUT_DIR = ROOT / "working"

SEASONS = list(range(2025, date.today().year + 1))


def load_json(name: str) -> dict:
    return json.loads((RAW_DIR / f"{name}.json").read_text())


def normalize(s: str) -> str:
    return s.strip().lower()


def build_driver_map():
    drivers = pd.read_csv(BASE_DIR / "drivers.csv")
    ref_to_id = dict(zip(drivers["driverRef"], drivers["driverId"]))
    next_id = int(drivers["driverId"].max()) + 1

    new_entries = []
    for season in SEASONS:
        data = load_json(f"drivers_{season}")
        for d in data.get("MRData", {}).get("DriverTable", {}).get("Drivers", []):
            ref = d["driverId"]  # jolpica's ref string
            if ref in ref_to_id:
                continue
            ref_to_id[ref] = next_id
            new_entries.append({
                "type": "driver",
                "ref": ref,
                "assigned_id": next_id,
                "code": d.get("code", ""),
                "forename": d.get("givenName", ""),
                "surname": d.get("familyName", ""),
                "dob": d.get("dateOfBirth", ""),
                "nationality": d.get("nationality", ""),
                "url": d.get("url", ""),
            })
            next_id += 1

    return ref_to_id, new_entries


def build_constructor_map():
    constructors = pd.read_csv(BASE_DIR / "constructors.csv")
    ref_to_id = dict(zip(constructors["constructorRef"], constructors["constructorId"]))
    next_id = int(constructors["constructorId"].max()) + 1

    new_entries = []
    for season in SEASONS:
        data = load_json(f"constructors_{season}")
        for c in data.get("MRData", {}).get("ConstructorTable", {}).get("Constructors", []):
            ref = c["constructorId"]
            if ref in ref_to_id:
                continue
            ref_to_id[ref] = next_id
            new_entries.append({
                "type": "constructor",
                "ref": ref,
                "assigned_id": next_id,
                "name": c.get("name", ""),
                "nationality": c.get("nationality", ""),
                "url": c.get("url", ""),
            })
            next_id += 1

    return ref_to_id, new_entries


def build_circuit_map():
    circuits = pd.read_csv(BASE_DIR / "circuits.csv")
    ref_to_id = dict(zip(circuits["circuitRef"], circuits["circuitId"]))
    next_id = int(circuits["circuitId"].max()) + 1

    new_entries = []
    for season in SEASONS:
        data = load_json(f"circuits_{season}")
        for c in data.get("MRData", {}).get("CircuitTable", {}).get("Circuits", []):
            ref = c["circuitId"]
            if ref in ref_to_id:
                continue
            loc = c.get("Location", {})
            ref_to_id[ref] = next_id
            new_entries.append({
                "type": "circuit",
                "ref": ref,
                "assigned_id": next_id,
                "name": c.get("circuitName", ""),
                "location": loc.get("locality", ""),
                "country": loc.get("country", ""),
                "lat": loc.get("lat", ""),
                "lng": loc.get("long", ""),
                "url": c.get("url", ""),
            })
            next_id += 1

    return ref_to_id, new_entries


def build_status_map():
    status_df = pd.read_csv(BASE_DIR / "status.csv")
    text_to_id = dict(zip(status_df["status"].map(normalize), status_df["statusId"]))
    display_text = dict(zip(status_df["status"].map(normalize), status_df["status"]))
    next_id = int(status_df["statusId"].max()) + 1

    new_entries = []
    seen_texts = set()
    for season in SEASONS:
        for f in RAW_DIR.glob(f"results_{season}_*.json"):
            data = json.loads(f.read_text())
            races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            for race in races:
                for res in race.get("Results", []):
                    status_text = res.get("status", "")
                    norm = normalize(status_text)
                    if norm in text_to_id or norm in seen_texts:
                        continue
                    seen_texts.add(norm)
                    text_to_id[norm] = next_id
                    new_entries.append({
                        "type": "status",
                        "ref": status_text,
                        "assigned_id": next_id,
                        "status_text": status_text,
                    })
                    next_id += 1

    return text_to_id, new_entries, display_text


def main():
    driver_map, new_drivers = build_driver_map()
    constructor_map, new_constructors = build_constructor_map()
    circuit_map, new_circuits = build_circuit_map()
    status_map, new_statuses, _ = build_status_map()

    (OUT_DIR / "id_maps.json").write_text(json.dumps({
        "driver_ref_to_id": driver_map,
        "constructor_ref_to_id": constructor_map,
        "circuit_ref_to_id": circuit_map,
        "status_text_to_id": status_map,
    }, indent=2))

    all_new = new_drivers + new_constructors + new_circuits + new_statuses
    new_df = pd.DataFrame(all_new)
    new_df.to_csv(OUT_DIR / "new_entities_log.csv", index=False)

    print(f"Driver map: {len(driver_map)} total, {len(new_drivers)} new")
    for e in new_drivers:
        print(f"  NEW DRIVER  id={e['assigned_id']:<5} ref={e['ref']:<20} {e['forename']} {e['surname']} ({e['nationality']})")

    print(f"\nConstructor map: {len(constructor_map)} total, {len(new_constructors)} new")
    for e in new_constructors:
        print(f"  NEW CONSTRUCTOR id={e['assigned_id']:<5} ref={e['ref']:<20} {e['name']} ({e['nationality']})")

    print(f"\nCircuit map: {len(circuit_map)} total, {len(new_circuits)} new")
    for e in new_circuits:
        print(f"  NEW CIRCUIT id={e['assigned_id']:<5} ref={e['ref']:<20} {e['name']} ({e['country']})")

    print(f"\nStatus map: {len(status_map)} total, {len(new_statuses)} new")
    for e in new_statuses:
        print(f"  NEW STATUS id={e['assigned_id']:<5} {e['status_text']}")

    print(f"\nFull log written to {OUT_DIR / 'new_entities_log.csv'}")
    print(f"ID maps written to {OUT_DIR / 'id_maps.json'}")


if __name__ == "__main__":
    main()

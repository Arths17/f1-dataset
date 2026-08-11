"""
Merge Jolpica-F1 2025-2026 data into the 14 base CSVs using the ID maps
from Step 3. Writes final merged CSVs to /output, preserving column order
and matching the base dataset's "\\N" null convention for string/object
columns.
"""
import json
from datetime import date, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BASE_DIR = ROOT / "working" / "base"
RAW_DIR = ROOT / "working" / "raw_jolpica"
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEASONS = [2025, 2026]
NA = "\\N"
TODAY = date.today()


def is_completed(race: dict) -> bool:
    race_date = race.get("date")
    if not race_date:
        return False
    return datetime.strptime(race_date, "%Y-%m-%d").date() < TODAY

id_maps = json.loads((ROOT / "working" / "id_maps.json").read_text())
driver_map = id_maps["driver_ref_to_id"]
constructor_map = id_maps["constructor_ref_to_id"]
circuit_map = id_maps["circuit_ref_to_id"]
status_map = id_maps["status_text_to_id"]


def load_json(name: str) -> dict:
    p = RAW_DIR / f"{name}.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def g(d, key, default=NA):
    v = d.get(key)
    return v if v not in (None, "") else default


# ---------- circuits.csv ----------
circuits = pd.read_csv(BASE_DIR / "circuits.csv")
existing_refs = set(circuits["circuitRef"])
new_circuit_rows = []
for season in SEASONS:
    data = load_json(f"circuits_{season}")
    for c in data.get("MRData", {}).get("CircuitTable", {}).get("Circuits", []):
        ref = c["circuitId"]
        if ref in existing_refs:
            continue
        existing_refs.add(ref)
        loc = c.get("Location", {})
        new_circuit_rows.append({
            "circuitId": circuit_map[ref],
            "circuitRef": ref,
            "name": c.get("circuitName", ""),
            "location": loc.get("locality", ""),
            "country": loc.get("country", ""),
            "lat": float(loc.get("lat", 0.0)),
            "lng": float(loc.get("long", 0.0)),
            "alt": 0,  # altitude not exposed by Jolpica; unknown for new circuits
            "url": c.get("url", ""),
        })
circuits_out = pd.concat([circuits, pd.DataFrame(new_circuit_rows)], ignore_index=True) if new_circuit_rows else circuits
circuits_out.to_csv(OUT_DIR / "circuits.csv", index=False)

# ---------- constructors.csv ----------
constructors = pd.read_csv(BASE_DIR / "constructors.csv")
existing_refs = set(constructors["constructorRef"])
new_rows = []
for season in SEASONS:
    data = load_json(f"constructors_{season}")
    for c in data.get("MRData", {}).get("ConstructorTable", {}).get("Constructors", []):
        ref = c["constructorId"]
        if ref in existing_refs:
            continue
        existing_refs.add(ref)
        new_rows.append({
            "constructorId": constructor_map[ref],
            "constructorRef": ref,
            "name": c.get("name", ""),
            "nationality": c.get("nationality", ""),
            "url": c.get("url", ""),
        })
constructors_out = pd.concat([constructors, pd.DataFrame(new_rows)], ignore_index=True) if new_rows else constructors
constructors_out.to_csv(OUT_DIR / "constructors.csv", index=False)

# ---------- drivers.csv ----------
drivers = pd.read_csv(BASE_DIR / "drivers.csv")
existing_refs = set(drivers["driverRef"])
new_rows = []
for season in SEASONS:
    data = load_json(f"drivers_{season}")
    for d in data.get("MRData", {}).get("DriverTable", {}).get("Drivers", []):
        ref = d["driverId"]
        if ref in existing_refs:
            continue
        existing_refs.add(ref)
        new_rows.append({
            "driverId": driver_map[ref],
            "driverRef": ref,
            "number": g(d, "permanentNumber"),
            "code": g(d, "code"),
            "forename": d.get("givenName", ""),
            "surname": d.get("familyName", ""),
            "dob": g(d, "dateOfBirth"),
            "nationality": g(d, "nationality", ""),
            "url": d.get("url", ""),
        })
drivers_out = pd.concat([drivers, pd.DataFrame(new_rows)], ignore_index=True) if new_rows else drivers
drivers_out.to_csv(OUT_DIR / "drivers.csv", index=False)

# ---------- status.csv ----------
status_df = pd.read_csv(BASE_DIR / "status.csv")
existing_status_norm = set(status_df["status"].str.strip().str.lower())
new_rows = []
for text_norm, sid in status_map.items():
    if text_norm in existing_status_norm:
        continue
    existing_status_norm.add(text_norm)
    new_rows.append({"statusId": sid, "status": text_norm.capitalize() if text_norm.islower() else text_norm})
# use log for correct casing
log_df = pd.read_csv(ROOT / "working" / "new_entities_log.csv")
status_log = log_df[log_df["type"] == "status"]
status_text_by_id = dict(zip(status_log["assigned_id"], status_log["status_text"]))
for row in new_rows:
    row["status"] = status_text_by_id.get(row["statusId"], row["status"])
status_out = pd.concat([status_df, pd.DataFrame(new_rows)], ignore_index=True) if new_rows else status_df
status_out.to_csv(OUT_DIR / "status.csv", index=False)

# ---------- seasons.csv ----------
seasons_df = pd.read_csv(BASE_DIR / "seasons.csv")
existing_years = set(seasons_df["year"])
new_rows = []
for season in SEASONS:
    if season in existing_years:
        continue
    new_rows.append({"year": season, "url": f"https://en.wikipedia.org/wiki/{season}_Formula_One_World_Championship"})
seasons_out = pd.concat([seasons_df, pd.DataFrame(new_rows)], ignore_index=True) if new_rows else seasons_df
seasons_out.to_csv(OUT_DIR / "seasons.csv", index=False)

# ---------- races.csv ----------
races_df = pd.read_csv(BASE_DIR / "races.csv")
next_race_id = int(races_df["raceId"].max()) + 1

race_rows = []
race_id_lookup = {}  # (season, round) -> raceId

for season in SEASONS:
    data = load_json(f"races_{season}")
    races = [r for r in data.get("MRData", {}).get("RaceTable", {}).get("Races", []) if is_completed(r)]
    races_sorted = sorted(races, key=lambda r: r["date"])
    for r in races_sorted:
        rnd = int(r["round"])
        race_id = next_race_id
        race_id_lookup[(season, rnd)] = race_id
        next_race_id += 1

        fp1 = r.get("FirstPractice", {})
        fp2 = r.get("SecondPractice", {})
        fp3 = r.get("ThirdPractice", {})
        quali = r.get("Qualifying", {})
        sprint = r.get("Sprint", {})

        race_rows.append({
            "raceId": race_id,
            "year": season,
            "round": rnd,
            "circuitId": circuit_map[r["Circuit"]["circuitId"]],
            "name": r.get("raceName", ""),
            "date": r.get("date", ""),
            "time": g(r, "time"),
            "url": r.get("url", ""),
            "fp1_date": g(fp1, "date"),
            "fp1_time": g(fp1, "time"),
            "fp2_date": g(fp2, "date"),
            "fp2_time": g(fp2, "time"),
            "fp3_date": g(fp3, "date"),
            "fp3_time": g(fp3, "time"),
            "quali_date": g(quali, "date"),
            "quali_time": g(quali, "time"),
            "sprint_date": g(sprint, "date"),
            "sprint_time": g(sprint, "time"),
        })

races_out = pd.concat([races_df, pd.DataFrame(race_rows)], ignore_index=True) if race_rows else races_df
races_out.to_csv(OUT_DIR / "races.csv", index=False)

# ---------- results.csv ----------
results_df = pd.read_csv(BASE_DIR / "results.csv")
next_result_id = int(results_df["resultId"].max()) + 1
result_rows = []
constructor_points_by_race = {}  # (raceId, constructorId) -> points sum, status flag

for season in SEASONS:
    for (s, rnd), race_id in list(race_id_lookup.items()):
        if s != season:
            continue
        data = load_json(f"results_{season}_{rnd}")
        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            continue
        for res in races[0].get("Results", []):
            drv = res["Driver"]["driverId"]
            con = res["Constructor"]["constructorId"]
            status_text = res.get("status", "")
            status_id = status_map.get(status_text.strip().lower())
            fastest = res.get("FastestLap", {})
            avg_speed = fastest.get("AverageSpeed", {})
            time_obj = res.get("Time", {})

            points = float(res.get("points", 0))
            result_rows.append({
                "resultId": next_result_id,
                "raceId": race_id,
                "driverId": driver_map[drv],
                "constructorId": constructor_map[con],
                "number": g(res, "number"),
                "grid": int(res.get("grid", 0)),
                "position": g(res, "position") if str(res.get("positionText", "")).isdigit() else NA,
                "positionText": res.get("positionText", ""),
                "positionOrder": int(res.get("positionText", 0)) if str(res.get("positionText", "")).isdigit() else 0,
                "points": points,
                "laps": int(res.get("laps", 0)),
                "time": g(time_obj, "time"),
                "milliseconds": g(time_obj, "millis"),
                "fastestLap": g(fastest, "lap"),
                "rank": g(fastest, "rank"),
                "fastestLapTime": g(fastest.get("Time", {}), "time"),
                "fastestLapSpeed": g(avg_speed, "speed"),
                "statusId": status_id,
            })
            next_result_id += 1

            key = (race_id, constructor_map[con])
            entry = constructor_points_by_race.setdefault(key, {"points": 0.0, "disqualified": False})
            entry["points"] += points
            if "disqualif" in status_text.lower():
                entry["disqualified"] = True

# fix positionOrder using actual finishing order (Ergast doesn't give raw order, use position if numeric else after all numeric)
results_new_df = pd.DataFrame(result_rows)
if not results_new_df.empty:
    pos_sort_key = results_new_df["position"].apply(lambda p: int(p) if p != NA else 999)
    results_new_df = results_new_df.assign(_pos_sort=pos_sort_key).sort_values(["raceId", "_pos_sort"])
    results_new_df["positionOrder"] = results_new_df.groupby("raceId").cumcount() + 1
    results_new_df = results_new_df.drop(columns="_pos_sort").sort_values("resultId").reset_index(drop=True)

results_out = pd.concat([results_df, results_new_df], ignore_index=True) if not results_new_df.empty else results_df
results_out.to_csv(OUT_DIR / "results.csv", index=False)

# ---------- constructor_results.csv ----------
cr_df = pd.read_csv(BASE_DIR / "constructor_results.csv")
next_cr_id = int(cr_df["constructorResultsId"].max()) + 1
cr_rows = []
for (race_id, con_id), entry in constructor_points_by_race.items():
    cr_rows.append({
        "constructorResultsId": next_cr_id,
        "raceId": race_id,
        "constructorId": con_id,
        "points": entry["points"],
        "status": "D" if entry["disqualified"] else NA,
    })
    next_cr_id += 1
cr_out = pd.concat([cr_df, pd.DataFrame(cr_rows)], ignore_index=True) if cr_rows else cr_df
cr_out.to_csv(OUT_DIR / "constructor_results.csv", index=False)

# ---------- qualifying.csv ----------
q_df = pd.read_csv(BASE_DIR / "qualifying.csv")
next_q_id = int(q_df["qualifyId"].max()) + 1
q_rows = []
for season in SEASONS:
    for (s, rnd), race_id in race_id_lookup.items():
        if s != season:
            continue
        data = load_json(f"qualifying_{season}_{rnd}")
        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            continue
        for res in races[0].get("QualifyingResults", []):
            q_rows.append({
                "qualifyId": next_q_id,
                "raceId": race_id,
                "driverId": driver_map[res["Driver"]["driverId"]],
                "constructorId": constructor_map[res["Constructor"]["constructorId"]],
                "number": int(res.get("number", 0)),
                "position": int(res.get("position", 0)),
                "q1": g(res, "Q1"),
                "q2": g(res, "Q2"),
                "q3": g(res, "Q3"),
            })
            next_q_id += 1
q_out = pd.concat([q_df, pd.DataFrame(q_rows)], ignore_index=True) if q_rows else q_df
q_out.to_csv(OUT_DIR / "qualifying.csv", index=False)

# ---------- sprint_results.csv ----------
sr_df = pd.read_csv(BASE_DIR / "sprint_results.csv")
next_sr_id = int(sr_df["resultId"].max()) + 1
sr_rows = []
for season in SEASONS:
    for (s, rnd), race_id in race_id_lookup.items():
        if s != season:
            continue
        data = load_json(f"sprint_{season}_{rnd}")
        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            continue
        for res in races[0].get("SprintResults", []):
            time_obj = res.get("Time", {})
            fastest = res.get("FastestLap", {})
            status_text = res.get("status", "")
            sr_rows.append({
                "resultId": next_sr_id,
                "raceId": race_id,
                "driverId": driver_map[res["Driver"]["driverId"]],
                "constructorId": constructor_map[res["Constructor"]["constructorId"]],
                "number": int(res.get("number", 0)),
                "grid": int(res.get("grid", 0)),
                "position": g(res, "position") if str(res.get("positionText", "")).isdigit() else NA,
                "positionText": res.get("positionText", ""),
                "positionOrder": int(res.get("positionText", 0)) if str(res.get("positionText", "")).isdigit() else 0,
                "points": int(float(res.get("points", 0))),
                "laps": int(res.get("laps", 0)),
                "time": g(time_obj, "time"),
                "milliseconds": g(time_obj, "millis"),
                "fastestLap": g(fastest, "lap"),
                "fastestLapTime": g(fastest.get("Time", {}), "time"),
                "statusId": status_map.get(status_text.strip().lower()),
            })
            next_sr_id += 1
sr_out = pd.concat([sr_df, pd.DataFrame(sr_rows)], ignore_index=True) if sr_rows else sr_df
sr_out.to_csv(OUT_DIR / "sprint_results.csv", index=False)

# ---------- pit_stops.csv ----------
ps_df = pd.read_csv(BASE_DIR / "pit_stops.csv")
ps_rows = []
for season in SEASONS:
    for (s, rnd), race_id in race_id_lookup.items():
        if s != season:
            continue
        data = load_json(f"pitstops_{season}_{rnd}")
        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            continue
        for ps in races[0].get("PitStops", []):
            ps_rows.append({
                "raceId": race_id,
                "driverId": driver_map[ps["driverId"]],
                "stop": int(ps.get("stop", 0)),
                "lap": int(ps.get("lap", 0)),
                "time": ps.get("time", ""),
                "duration": g(ps, "duration"),
                "milliseconds": int(float(ps["duration"]) * 1000) if ps.get("duration") and ps["duration"].replace(".", "", 1).isdigit() else 0,
            })
ps_out = pd.concat([ps_df, pd.DataFrame(ps_rows)], ignore_index=True) if ps_rows else ps_df
ps_out.to_csv(OUT_DIR / "pit_stops.csv", index=False)

# ---------- lap_times.csv ----------
lt_df = pd.read_csv(BASE_DIR / "lap_times.csv")
lt_rows = []
for season in SEASONS:
    for (s, rnd), race_id in race_id_lookup.items():
        if s != season:
            continue
        data = load_json(f"laps_{season}_{rnd}")
        races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
        if not races:
            continue
        for lap in races[0].get("Laps", []):
            lap_num = int(lap["number"])
            for timing in lap.get("Timings", []):
                t = timing["time"]
                minutes, rest = (t.split(":") + [None])[:2] if ":" in t else (None, t)
                millis = 0
                try:
                    if minutes is not None:
                        m = int(minutes)
                        sec = float(rest)
                        millis = m * 60000 + int(round(sec * 1000))
                    else:
                        millis = int(round(float(rest) * 1000))
                except (ValueError, TypeError):
                    millis = 0
                lt_rows.append({
                    "raceId": race_id,
                    "driverId": driver_map[timing["driverId"]],
                    "lap": lap_num,
                    "position": int(timing.get("position", 0)),
                    "time": t,
                    "milliseconds": millis,
                })
lt_out = pd.concat([lt_df, pd.DataFrame(lt_rows)], ignore_index=True) if lt_rows else lt_df
lt_out.to_csv(OUT_DIR / "lap_times.csv", index=False)

# ---------- driver_standings.csv ----------
ds_df = pd.read_csv(BASE_DIR / "driver_standings.csv")
next_ds_id = int(ds_df["driverStandingsId"].max()) + 1
ds_rows = []
for season in SEASONS:
    for (s, rnd), race_id in race_id_lookup.items():
        if s != season:
            continue
        data = load_json(f"driverStandings_{season}_{rnd}")
        lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
        if not lists:
            continue
        for st in lists[0].get("DriverStandings", []):
            ds_rows.append({
                "driverStandingsId": next_ds_id,
                "raceId": race_id,
                "driverId": driver_map[st["Driver"]["driverId"]],
                "points": float(st.get("points", 0)),
                "position": int(st.get("position", 0)),
                "positionText": st.get("positionText", ""),
                "wins": int(st.get("wins", 0)),
            })
            next_ds_id += 1
ds_out = pd.concat([ds_df, pd.DataFrame(ds_rows)], ignore_index=True) if ds_rows else ds_df
ds_out.to_csv(OUT_DIR / "driver_standings.csv", index=False)

# ---------- constructor_standings.csv ----------
cs_df = pd.read_csv(BASE_DIR / "constructor_standings.csv")
next_cs_id = int(cs_df["constructorStandingsId"].max()) + 1
cs_rows = []
for season in SEASONS:
    for (s, rnd), race_id in race_id_lookup.items():
        if s != season:
            continue
        data = load_json(f"constructorStandings_{season}_{rnd}")
        lists = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
        if not lists:
            continue
        for st in lists[0].get("ConstructorStandings", []):
            cs_rows.append({
                "constructorStandingsId": next_cs_id,
                "raceId": race_id,
                "constructorId": constructor_map[st["Constructor"]["constructorId"]],
                "points": float(st.get("points", 0)),
                "position": int(st.get("position", 0)),
                "positionText": st.get("positionText", ""),
                "wins": int(st.get("wins", 0)),
            })
            next_cs_id += 1
cs_out = pd.concat([cs_df, pd.DataFrame(cs_rows)], ignore_index=True) if cs_rows else cs_df
cs_out.to_csv(OUT_DIR / "constructor_standings.csv", index=False)

print("Merge complete. Files written to", OUT_DIR)
for f in sorted(OUT_DIR.glob("*.csv")):
    print(f"  {f.name}: {sum(1 for _ in open(f)) - 1} rows")

# Schema

Full column reference for all 17 tables in this dataset.

## races.csv

One row per race: season, round, circuit, name, date/time, and practice/qualifying/sprint session schedule.

| Column | Description |
|---|---|
| `raceId` | Unique identifier for the race (primary key). |
| `year` | Championship season. |
| `round` | Round number within that season. |
| `circuitId` | Foreign key to circuits.csv. |
| `name` | Official race name, e.g. 'Monaco Grand Prix'. |
| `date` | Race date (YYYY-MM-DD). |
| `time` | Race start time (UTC), or \N if unknown. |
| `url` | Wikipedia page for the race. |
| `fp1_date` | Free Practice 1 date. |
| `fp1_time` | Free Practice 1 start time (UTC). |
| `fp2_date` | Free Practice 2 date. |
| `fp2_time` | Free Practice 2 start time (UTC). |
| `fp3_date` | Free Practice 3 date. |
| `fp3_time` | Free Practice 3 start time (UTC). |
| `quali_date` | Qualifying session date. |
| `quali_time` | Qualifying session start time (UTC). |
| `sprint_date` | Sprint race date, or \N if the weekend had no sprint. |
| `sprint_time` | Sprint race start time (UTC), or \N. |

## results.csv

Race classification results: grid position, finishing position, points, laps, race time, fastest lap, and finishing status per driver per race.

| Column | Description |
|---|---|
| `resultId` | Unique identifier for the result row (primary key). |
| `raceId` | Foreign key to races.csv. |
| `driverId` | Foreign key to drivers.csv. |
| `constructorId` | Foreign key to constructors.csv. |
| `number` | Car number used in this race. |
| `grid` | Starting grid position. |
| `position` | Final classified finishing position, or \N if unclassified (DNF/DSQ/etc). |
| `positionText` | Finishing position as text; non-numeric codes like 'R' (retired), 'D' (disqualified), 'W' (withdrew) for unclassified results. |
| `positionOrder` | Numeric finishing order for sorting (classified drivers first, by position, then unclassified). |
| `points` | Championship points scored. |
| `laps` | Laps completed. |
| `time` | Race finishing time (leader) or gap to leader, or \N if not applicable. |
| `milliseconds` | Race time in milliseconds, or \N. |
| `fastestLap` | Lap number of the driver's fastest lap, or \N. |
| `rank` | Rank of this driver's fastest lap among all drivers in the race, or \N. |
| `fastestLapTime` | Fastest lap time, or \N. |
| `fastestLapSpeed` | Average speed on the fastest lap (km/h), or \N. Not available from the data source for 2025/2026 races. |
| `statusId` | Foreign key to status.csv describing how the race ended for this driver. |

## qualifying.csv

Qualifying session results per driver per race, including Q1/Q2/Q3 times and grid position.

| Column | Description |
|---|---|
| `qualifyId` | Unique identifier for the qualifying result (primary key). |
| `raceId` | Foreign key to races.csv. |
| `driverId` | Foreign key to drivers.csv. |
| `constructorId` | Foreign key to constructors.csv. |
| `number` | Car number used in qualifying. |
| `position` | Qualifying position, which sets the starting grid. |
| `q1` | Q1 session lap time, or \N if not set. |
| `q2` | Q2 session lap time, or \N if the driver didn't advance to Q2. |
| `q3` | Q3 session lap time, or \N if the driver didn't advance to Q3. |

## sprint_results.csv

Sprint race classification results, same structure as results.csv, for race weekends with a sprint format.

| Column | Description |
|---|---|
| `resultId` | Unique identifier for the sprint result (primary key). |
| `raceId` | Foreign key to races.csv. |
| `driverId` | Foreign key to drivers.csv. |
| `constructorId` | Foreign key to constructors.csv. |
| `number` | Car number used in the sprint. |
| `grid` | Sprint starting grid position. |
| `position` | Final classified sprint finishing position, or \N if unclassified. |
| `positionText` | Finishing position as text; non-numeric codes for unclassified results. |
| `positionOrder` | Numeric finishing order for sorting. |
| `points` | Championship points scored in the sprint. |
| `laps` | Laps completed. |
| `time` | Sprint finishing time (leader) or gap to leader, or \N. |
| `milliseconds` | Sprint time in milliseconds, or \N. |
| `fastestLap` | Lap number of the driver's fastest lap in the sprint, or \N. |
| `fastestLapTime` | Fastest sprint lap time, or \N. |
| `statusId` | Foreign key to status.csv describing how the sprint ended for this driver. |

## pit_stops.csv

Individual pit stop records: which lap, stop number, time of day, and duration per driver per race.

| Column | Description |
|---|---|
| `raceId` | Foreign key to races.csv. |
| `driverId` | Foreign key to drivers.csv. |
| `stop` | Stop number for this driver in this race (1st stop, 2nd stop, etc). |
| `lap` | Lap on which the stop occurred. |
| `time` | Time of day the stop occurred. |
| `duration` | Pit stop duration in seconds. |
| `milliseconds` | Pit stop duration in milliseconds. |

## lap_times.csv

Lap-by-lap timing per driver per race (position and time each lap). Does not yet include 2025/2026 data - see README.

| Column | Description |
|---|---|
| `raceId` | Foreign key to races.csv. |
| `driverId` | Foreign key to drivers.csv. |
| `lap` | Lap number. |
| `position` | Driver's race position at the end of this lap. |
| `time` | Lap time. |
| `milliseconds` | Lap time in milliseconds. |

## driver_standings.csv

Championship standings for drivers after each race: cumulative points, position, and wins.

| Column | Description |
|---|---|
| `driverStandingsId` | Unique identifier for this standings row (primary key). |
| `raceId` | Foreign key to races.csv - standings as of after this race. |
| `driverId` | Foreign key to drivers.csv. |
| `points` | Cumulative championship points through this race. |
| `position` | Championship standing position. |
| `positionText` | Standing position as text. |
| `wins` | Cumulative race wins through this race. |

## constructor_standings.csv

Championship standings for constructors (teams) after each race: cumulative points, position, and wins.

| Column | Description |
|---|---|
| `constructorStandingsId` | Unique identifier for this standings row (primary key). |
| `raceId` | Foreign key to races.csv - standings as of after this race. |
| `constructorId` | Foreign key to constructors.csv. |
| `points` | Cumulative championship points through this race. |
| `position` | Championship standing position. |
| `positionText` | Standing position as text. |
| `wins` | Cumulative race wins through this race. |

## constructor_results.csv

Points scored by each constructor in each race, aggregated across both of their drivers.

| Column | Description |
|---|---|
| `constructorResultsId` | Unique identifier for this row (primary key). |
| `raceId` | Foreign key to races.csv. |
| `constructorId` | Foreign key to constructors.csv. |
| `points` | Total points scored by the constructor in this race. |
| `status` | 'D' if the constructor was disqualified from this race, otherwise \N. |

## drivers.csv

Driver lookup table: name, code, permanent number, date of birth, and nationality.

| Column | Description |
|---|---|
| `driverId` | Unique identifier for the driver (primary key). |
| `driverRef` | URL-safe reference slug for the driver. |
| `number` | Permanent car number, or \N if none assigned. |
| `code` | Three-letter driver code, or \N if none assigned. |
| `forename` | Driver's given name. |
| `surname` | Driver's family name. |
| `dob` | Date of birth. |
| `nationality` | Driver's nationality. |
| `url` | Wikipedia page for the driver. |

## constructors.csv

Constructor (team) lookup table: name and nationality.

| Column | Description |
|---|---|
| `constructorId` | Unique identifier for the constructor (primary key). |
| `constructorRef` | URL-safe reference slug for the constructor. |
| `name` | Constructor/team name. |
| `nationality` | Constructor's nationality. |
| `url` | Wikipedia page for the constructor. |

## circuits.csv

Circuit lookup table: name, location, country, and geographic coordinates.

| Column | Description |
|---|---|
| `circuitId` | Unique identifier for the circuit (primary key). |
| `circuitRef` | URL-safe reference slug for the circuit. |
| `name` | Circuit name. |
| `location` | City or locality. |
| `country` | Country. |
| `lat` | Latitude. |
| `lng` | Longitude. |
| `alt` | Altitude in meters. Set to 0 as a placeholder for circuits added after 2024 where this data isn't available from the source API. |
| `url` | Wikipedia page for the circuit. |

## seasons.csv

One row per championship season (year), with a link to that season's overview.

| Column | Description |
|---|---|
| `year` | Championship season (primary key). |
| `url` | Wikipedia page for that season. |

## status.csv

Lookup table of race finishing status codes (e.g. Finished, Retired, Disqualified, Did not start).

| Column | Description |
|---|---|
| `statusId` | Unique identifier for the status (primary key). |
| `status` | Human-readable status text, referenced by results.csv and sprint_results.csv. |

## practice_results.csv

Free practice (FP1/FP2/FP3) session results per driver per race, sourced from official F1 live timing via FastF1. Covers only the 2025/2026 races added by this extension - not available for 1950-2024. Reserve/test drivers who ran practice sessions but didn't race are not included, since they aren't in drivers.csv.

| Column | Description |
|---|---|
| `raceId` | Foreign key to races.csv. |
| `driverId` | Foreign key to drivers.csv. |
| `session` | Which practice session: FP1, FP2, or FP3. |
| `position` | Rank within the session by best lap time (1 = fastest). |
| `bestLapTime` | Driver's fastest lap time in this session. |
| `laps` | Number of laps completed in this session. |

## weather.csv

Per-race weather summary (aggregated from minute-by-minute samples), sourced from official F1 live timing via FastF1. Covers only the 2025/2026 races added by this extension - not available for 1950-2024.

| Column | Description |
|---|---|
| `raceId` | Foreign key to races.csv. |
| `airTempAvg` | Average air temperature during the race (°C). |
| `airTempMin` | Minimum air temperature during the race (°C). |
| `airTempMax` | Maximum air temperature during the race (°C). |
| `trackTempAvg` | Average track surface temperature during the race (°C). |
| `trackTempMin` | Minimum track surface temperature during the race (°C). |
| `trackTempMax` | Maximum track surface temperature during the race (°C). |
| `humidityAvg` | Average relative humidity during the race (%). |
| `windSpeedAvg` | Average wind speed during the race (m/s). |
| `windSpeedMax` | Maximum wind speed during the race (m/s). |
| `rainfall` | True if rain was recorded at any point during the race. |

## tire_stints.csv

Tire strategy per driver per race, sourced from official F1 live timing via FastF1. Covers only the 2025/2026 races added by this extension - not available for 1950-2024.

| Column | Description |
|---|---|
| `raceId` | Foreign key to races.csv. |
| `driverId` | Foreign key to drivers.csv. |
| `stint` | Stint number for this driver in this race (1st stint, 2nd stint, etc). |
| `compound` | Tire compound used this stint (SOFT, MEDIUM, HARD, INTERMEDIATE, WET), or \N if unknown. |
| `startLap` | First lap of this stint. |
| `endLap` | Last lap of this stint. |
| `lapsOnTire` | Number of laps completed on this set of tires (endLap - startLap + 1). |

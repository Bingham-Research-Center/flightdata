# ADS-B Research Notes (Flightdata)

## What this repo does
`adsbdecoder.py` connects to a live Beast TCP feed, decodes ADS‑B/Comm‑B, and writes two Parquet files: `adsb_core.parquet` and `adsb_derived.parquet`.

## Output & “schema” in plain language
Think of a **schema** as the small, fixed set of columns we keep on purpose.  
We keep only the most useful fields, then compute extra (derived) fields from them.

Recommended split:
- **Core file**: raw‑core columns (time, position, key identifiers).
- **Derived file**: computed features (wind, stability, turbulence proxies).

## Units (simple rule)
- Pick **SI units** as the default and convert at ingest.
- If we keep aviation units, we **label them** (`_kt`, `_ft`, `_hpa`).
- See `units.md` for the column→unit mapping.

## Raw messages (avoid duplicates)
We keep a short `msg_hash` to deduplicate and trace anomalies without storing full raw hex.  
This allows dropping `msg` later while still preventing duplicate rows.

## Research planning
- Detailed derived‑feature plan and hypotheses live in `DERIVED_FEATURES.md`.
- This keeps the repo small while still documenting the scientific direction.

## Prototypes to build next (overview)
1) Wind vector from airspeed vs. groundspeed  
2) Lapse‑rate / inversion detection  
3) Turbulence and shear proxies  
4) Cold‑pool and basin stability signals  

## Helpers (terse)
- Summary: `python tools/summary.py`  
  - Defaults to `adsb_core.parquet` + `adsb_derived.parquet`
- CSV import: `python tools/import_csv.py example_output.csv`

## SOP (terse)
- Keep `msg_hash` in both files for dedup and joins.  
- Join core + derived on `(icao, timestamp, msg_hash)`.  
- Keep `units.md` updated when adding columns.

## Run
`python adsbdecoder.py`

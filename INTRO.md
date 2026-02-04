# Project Intro (Plain Language)

## What we have
- A live ADS‑B/Comm‑B decoder (`adsbdecoder.py`) that writes two Parquet files:
  - `adsb_core.parquet` (core raw fields)
  - `adsb_derived.parquet` (future derived fields)
- A research plan for derived features in `DERIVED_FEATURES.md`.
- A units map in `units.md`.

## Science questions (short list)
- Can aircraft data reveal wind, stability, and inversion structure over a mountain basin?
- Can we detect cold‑pool formation/breakup from vertical profiles and time changes?
- Can turbulence proxies or wind‑shear signals be extracted from flight tracks?

## What’s likely to work (high viability)
- Wind vector estimates where heading + airspeed exist.
- Basin‑scale stability signals when we have enough low‑altitude traffic.
- Turbulence proxies based on variability of vertical rate and track.

## Stretch goals (medium/low viability)
- Full thermodynamic profiles (needs frequent Comm‑B weather messages).
- Robust lapse‑rate estimation at fine vertical resolution (needs dense flights).
- Change‑point detection of air‑mass transitions (needs long time series).

## Outstanding experiments
- Collect longer live streams to see how often Comm‑B weather appears.
- Measure how much data exists below ~5,000 ft AGL in the basin.
- Prototype wind + lapse‑rate features and validate against known weather.
- UAT exploration with new antenna/receiver hardware to see which new message types or quality improvements appear.

## Open questions
- How often do local aircraft broadcast BDS 4,4/4,5?
- What spatial/temporal bin sizes are stable for this region?
- What precision is “enough” without losing useful signal?
- Do the new receivers increase DF 20/21 coverage or improve low‑altitude signal quality?

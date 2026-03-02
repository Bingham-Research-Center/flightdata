# Flightdata: Uinta Basin Aircraft Signals for Weather Research

## Why this exists
The Uinta Basin has sparse in-situ atmospheric observations for some key questions, especially winter cold pools and low-level stability changes.
This project tests whether aircraft broadcasts can add useful time-height information to reduce uncertainty in those conditions.

## Who this README is for
- Primary: collaborators (current and future) who need a plain-language project map.
- Secondary: proposal-oriented readers who need to see why this is fundable and technically credible.

## Quick links
- Project home: https://github.com/Bingham-Research-Center/flightdata
- Data-play notebook: `notebooks/uinta_basin_proof_of_concept.ipynb`
- Sample data file: https://github.com/Bingham-Research-Center/flightdata/blob/main/example_output.csv
- Feature roadmap: `DERIVED_FEATURES.md`
- Units map: `units.md`

## Current proof of concept
- We decode live ADS-B/Mode-S streams from local antenna access (Vernal/KVEL area context).
- We already extract robust core fields (time, aircraft id, position, motion).
- We also decode richer Comm-B fields when present (including candidate meteorological/hazard-related channels).
- We can write compact parquet outputs and quickly inventory field availability.

This is enough to justify follow-on work: we have real data, real coverage, and real derived-variable opportunities.

## Data access right now
- Live raw capture is currently local-network only.
- The decoder writes:
  - `adsb_core.parquet`
  - `adsb_derived.parquet`
- A sample file is in-repo for off-site exploration:
  - `example_output.csv`

## One-command capture length control
Set capture duration directly:

`python adsbdecoder.py --seconds 60`

Other useful options:

`python adsbdecoder.py --host 129.123.91.145 --port 30005 --seconds 120 --core-out adsb_core.parquet --derived-out adsb_derived.parquet`

## Notebook workflow
The notebook (`notebooks/uinta_basin_proof_of_concept.ipynb`) will:
- Load local real captures when available.
- Fall back to `example_output.csv` when local parquet files are absent.
- Produce plain tables/plots for:
  - Field availability inventory.
  - Message-type mix.
  - Time coverage.
  - Spatial footprint (coverage cone style view).
  - Altitude distribution (with caveats about MSL vs AGL interpretation).

## Research direction (plain language)
1. Collect longer and targeted windows to characterize intermittent traffic and data richness.
2. Prioritize variables that can tighten uncertainty quickly (wind/stability proxies first).
3. Quantify what is sparse and needs targeted capture.
4. Build defensible evidence for funding proposals and future publications.

## UAT and future expansion
UAT (978 MHz, especially relevant to GA traffic) is a likely near-term expansion.
We do not claim strong UAT expertise yet; we treat it as a high-value question for aviation collaborators.

Potential strategic extension:
- Add a second receiver near Roosevelt to improve low-level sampling geometry west of Vernal.

## Open questions for collaborators
- What capture strategy best represents intermittent KVEL arrivals/departures?
- Which derived variables are strongest early signals for reviewers?
- How should we validate low-level profile signals for cold-pool detection?
- What does UAT likely add in this region and traffic mix?
- What is the minimum evidence threshold for a preprint and funding case?

## Funding statement (short)
This project targets a practical gap: extracting atmospheric value from existing aircraft broadcasts in a data-sparse region.
The immediate ask is support for expanded collection, validation, and targeted hardware/logging improvements that can convert this proof of concept into an operational research product.

## Minimal run commands
Preferred setup (Miniforge/mamba):

`mamba create -y -n flightdata python=3.11 polars pandas matplotlib pyarrow jupyterlab pymodes`
`mamba activate flightdata`

Pip fallback:

`pip install pyModeS polars pandas matplotlib pyarrow`

Capture:

`python adsbdecoder.py --seconds 60`

Summarize parquet:

`python tools/summary.py`

Convert sample CSV to parquet if needed:

`python tools/import_csv.py example_output.csv`

## AI use transparency
AI is used heavily during prototyping and brainstorming in this phase.
Scientific interpretation, project direction, and final wording are reviewed by humans and should become increasingly human-led as the project matures.

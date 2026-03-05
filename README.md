# Flightdata: ADS-B for Uinta Basin Cold-Pool Research

## Project Purpose

This repo is not a standard ADS-B tracking project.  
It tests whether aircraft broadcasts can add useful atmospheric structure in a data-sparse basin, especially for winter cold pools and stability transitions.

Target users here already know ADS-B and Mode-S mechanics; this README focuses on why the weather use case is different and what to do next.

## What This Project Has (Now)

- Live decode pipeline to parquet (`adsbdecoder.py`).
- Core and derived outputs with stable join keys.
- In-repo sample files for reproducible collaborator analysis.
- Notebook for fast field-availability and coverage inspection.

Key in-repo sample snapshot (March 2, 2026, 60s):

- 13,252 rows, 72 aircraft.
- DF17 only in that sample.
- Strong high-altitude kinematics.
- No low-level rows in basin-relevant bands.
- No observed Comm-B met/hazard yield in that sample.

Meaning: pipeline feasibility is demonstrated; low-level cold-pool detection is not yet demonstrated.

## Why This Use Case Is Harder Than Typical ADS-B Work

- Atmospheric inference needs low-level vertical sampling, not just traffic presence.
- Cold-pool diagnosis needs nighttime and terrain-aware coverage.
- Comm-B met channels can be sparse or absent depending on fleet/region.
- Geometry matters: one receiver can miss key low-level paths.

## Repository Map

- `adsbdecoder.py`: capture + decode entry point.
- `DERIVED_FEATURES.md`: feature roadmap with evidence-for/evidence-against notes.
- `units.md`: unit conventions.
- `DATA_PLAYBOOK.md`: parquet workflow and collaborator data handling.
- `notebooks/uinta_basin_proof_of_concept.ipynb`: first-pass inventory notebook.
- `example_2026-03-02_60s_core.parquet`
- `example_2026-03-02_60s_derived.parquet`
- `SCIENTIFIC_REVIEW.md`: current viability review and next-batch priorities.

## Quick Start

Environment (mamba preferred):

`mamba create -y -n flightdata python=3.11 polars pandas matplotlib pyarrow jupyterlab pymodes`  
`mamba activate flightdata`

Pip fallback:

`pip install pyModeS polars pandas matplotlib pyarrow`

Capture:

`python adsbdecoder.py --seconds 60`

Summarize outputs:

`python tools/summary.py adsb_core.parquet adsb_derived.parquet`

Create shareable snapshot:

`python tools/make_collab_snapshot.py --core-in adsb_core.parquet --derived-in adsb_derived.parquet --prefix example_YYYY-MM-DD_60s`

Render docs to PDF:

`python tools/render_markdown_pdf.py README.md --out README.pdf`  
`python tools/render_markdown_pdf.py DERIVED_FEATURES.md --out DERIVED_FEATURES.pdf`

## Collaborator Priorities (Recommended Order)

1. Quantify low-level sufficiency near KVEL (altitude-distance-time bins).
2. Quantify Comm-B yield over longer windows.
3. Run targeted arrival/departure and overnight capture windows.
4. Add terrain-relative altitude proxy and re-evaluate low-level coverage.
5. Validate one case against independent observations.

## Evidence Guardrails

- Do not claim cold-pool detection from current in-repo sample alone.
- Treat Comm-B meteorology as measured availability, not assumed availability.
- Gate feature expansion on coverage sufficiency first.

## Configuration Notes

Receiver defaults are in `adsbdecoder.py` (`host`, `port`, `ref_lat`, `ref_lon`).
Keep site-specific settings out of shared commits unless needed.

## AI Transparency

AI support is used in prototyping and drafting.
Scientific interpretation and final project direction are human-reviewed.

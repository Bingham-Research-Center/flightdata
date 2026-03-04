# Scientific Review: ADS-B for Uinta Basin Cold-Pool Detection (Skeptical Reviewer Lens)

Date: March 4, 2026

## Project Overview for Newcomers

This repository is a focused feasibility project: can passive aircraft broadcasts help diagnose basin weather structure (especially winter cold pools) where in-situ observations are sparse?

The project already has useful building blocks:

- A working decoder for live Beast-feed traffic (`adsbdecoder.py`) with core and derived parquet outputs.
- In-repo sample capture files (`example_2026-03-02_60s_core.parquet`, `example_2026-03-02_60s_derived.parquet`).
- A collaborator notebook (`notebooks/uinta_basin_proof_of_concept.ipynb`) for quick exploratory analysis.
- A clear feature hypothesis roadmap (`DERIVED_FEATURES.md`) and unit mapping (`units.md`).

In plain terms: this is a functional prototype data pipeline, but atmospheric inference claims are still premature.

## What the Current Evidence Actually Shows

From the in-repo March 2, 2026 sample (about one minute, 22:45:05 to 22:46:04 UTC):

- 13,252 decoded rows from 72 unique aircraft.
- Message family in this sample: DF17 only.
- Position decode success: 9,252 / 13,252 rows (69.8%).
- Altitude non-null rows: 4,743.
- Altitude range (non-null): 20,375 to 47,000 ft (MSL).
- Rows at or below 7,000 ft: 0 / 4,743.
- Relative to the decoder reference coordinates (KVEL-area context), this sample has no positioned rows within 20 km; nearest positioned rows are about 24 km away and around 38,000 ft.
- Candidate Comm-B met/hazard fields in the notebook inventory (`wind44`, `temp44`, `p44`, `hum44`, `temp45`, `p45`, `rh45`, `turb45`, `ws45`, `roll50`, `trk50`, `tas50`, `ias60`, `mach60`): all zero in this sample.
- Velocity type appears as `GS` (ground-speed form), with no airspeed-type evidence in this sample.

Interpretation:

- The pipeline clearly works.
- The sample demonstrates high-altitude en-route traffic, not near-surface basin structure.
- The sample does not demonstrate low-level approach/departure sampling at KVEL-scale altitudes.
- The sample does not demonstrate meteorological Comm-B availability.
- Evidence here is sufficient for feasibility motivation, not for detection-performance claims.

## Scientific Viability Assessment (Neutral)

### For detecting low-level cold pools now

Current viability is low with present evidence, and likely not defensible to a skeptical panel yet.

Reason:

- Cold-pool diagnosis needs low-level vertical structure (near basin floor and lower boundary layer).
- The in-repo sample has no low-altitude rows and no direct thermodynamic fields.
- One minute of data cannot represent nocturnal buildup, persistence, and breakup phases.

### For extracting useful information from ADS-B overall

Current viability is moderate for engineering/data-product development, but low-to-moderate for direct meteorological inference.

What is already viable:

- Traffic/time-height inventory and coverage diagnostics.
- Repeatable ingestion and quality-screening framework.
- Upper-level kinematic context and platform for future derived features.

What is not yet evidenced:

- Robust near-surface profile sampling in the target region.
- Reliable Comm-B meteorological channels in this local traffic/radar environment.
- Independent validation against ground truth for cold-pool signal detection.

## Does the Project Need Longer Sampling (Including KVEL Landings)?

Yes, clearly and non-negotiably.

If the scientific target is low-level cold pools, minutes are not scientifically meaningful. The minimum dataset is sustained multi-week to seasonal capture, with targeted windows around expected local arrivals/departures and nighttime cold-pool periods.

Recommended sampling design:

1. Continuous 1090 capture for at least 30-60 days to measure true low-level opportunity rate.
2. Targeted KVEL windows: scheduled/typical arrival-departure periods plus sunset-to-sunrise periods during likely cold-pool nights.
3. Keep raw-message retention for selected validation windows (do not only keep compact snapshots).
4. Add UAT/978 capture if possible; low-level GA traffic is likely critical in this region.
5. Strongly consider a second receiver geometry (e.g., Roosevelt side) to improve low-level basin coverage.

## Key Risks to State Openly

- Comm-B meteorological fields may remain very sparse in this region even with longer captures.
- A single receiver may under-sample low-level basin structure due to geometry and line-of-sight limitations.
- ADS-B alone may not recover full thermodynamic state without additional validation data.

These are not minor caveats; they are project-limiting uncertainties until tested directly.

## What Would Make This Persuasive for Funding

The project is fundable only if framed as a staged feasibility-to-validation effort, not as a finished detection system.

Strong points already present:

- Working code and reproducible parquet outputs.
- Clear science hypotheses and phased roadmap.
- Real decoded data, not synthetic-only development.

Gaps that should be closed before strong claims:

- Demonstrate repeated low-level profiles near KVEL/basin floor.
- Quantify actual Comm-B yield over longer periods.
- Show at least one validated case study against independent observations (surface stations, ceilometer/profiler/radiosonde/reanalysis).

Suggested milestone gates before major proposal claims:

1. Data sufficiency gate: enough low-level profiles over enough nights.
2. Signal gate: derived indicators separate known cold-pool vs non-cold-pool periods.
3. Validation gate: agreement with at least one independent dataset and uncertainty bounds.

## Bottom-Line Judgement

This repository is a credible and well-structured prototype with a clear scientific direction.

As of March 4, 2026 evidence, it does not yet support strong claims of low-level cold-pool detection from ADS-B in the Uinta Basin.

It does support funding a next phase focused on longer targeted sampling, low-level traffic capture (likely including UAT), geometry improvements, and validation. That is the scientifically honest and persuasive path forward.

## Extensions to the Prelim Work (Next Batch)

Low-hanging extensions below are ordered by urgency/importance (highest first). Most are feasible within current project time and current data workflow; collaborators can append rows to this same table.

| Priority | Extension | Why this is urgent (skeptical gap) | Effort | Who can do it now | Concrete output |
|---|---|---|---|---|---|
| 1 | Low-level sufficiency audit near KVEL | Current sample has no low-level evidence; must quantify this directly before further claims. | Low | Project lead or collaborator with parquet access | Table/plot: counts by altitude bands, distance-to-KVEL bands, hour-of-day |
| 2 | Comm-B yield audit across all existing captures | Current met/hazard fields are zero in sample; need hard yield numbers before promising those features. | Low | Anyone with local/archive parquet files | Coverage table: non-null rates for BDS 4,4 / 4,5 / 5,0 / 6,0 fields |
| 3 | Targeted landing/departure window test (KVEL) | Need evidence that approach/departure traffic exists often enough to sample basin-relevant levels. | Low-Med | Local receiver operator | 1-2 week pilot summary of low-altitude hit rate during targeted windows |
| 4 | Terrain-relative altitude (AGL proxy) pass | MSL altitude alone is weak for cold-pool interpretation in basin terrain. | Med | Notebook contributor | Derived `altitude_agl_proxy` and updated low-level histograms/maps |
| 5 | False-positive stress test on “cold-pool indicators” | Prevent overclaiming: show how often indicators trigger on non-event periods. | Med | Analysis collaborator | Precision-style table for candidate indicators on control periods |
| 6 | One anchored validation case study | Claims are weak without external comparison to independent observations. | Med | Science lead + data analyst | Single event brief: ADS-B-derived signals vs station/reanalysis timeline |
| 7 | Receiver-geometry sensitivity note | Single-receiver blind spots may dominate conclusions; reviewers will ask this immediately. | Med | Collaborator with mapping skills | Short memo + map: observed footprint limits and likely missing zones |
| 8 | Open table maintenance for collaborators | Keeps scope explicit and prevents ad hoc claim creep. | Low | Any contributor | Added rows with same columns + date/owner for each new task |

Suggested done rule for each row: include one figure/table plus a one-paragraph finding with explicit “supported / not supported / inconclusive” language.

# Scientific Review: ADS-B for Uinta Basin Cold-Pool Detection

Reviewer: gpt-codex-5.3-xhigh  
Date: March 4, 2026

## Scope and Materials

This project is testing whether aircraft broadcast data can add useful boundary-layer information in a sparse-observation basin environment.

Current repo assets are strong for a prelim phase:

- Working decoder and parquet pipeline (adsbdecoder.py).
- Reproducible sample data (example March 2 core/derived parquet snapshots).
- Quick analysis notebook for collaborators.
- Clear feature and units docs (DERIVED_FEATURES.md, units.md).

Assessment: engineering readiness is good; atmospheric claim readiness is still early.

## What the Current Data Proves

In-repo sample window (March 2, 2026, about 1 minute):

- 13,252 rows, 72 aircraft.
- DF17 only in this sample.
- Position decode rate: 69.8%.
- Non-null altitude rows: 4,743.
- Altitude range: 20,375 to 47,000 ft MSL.
- Rows at or below 7,000 ft: 0.
- Near KVEL-area reference coordinates: no positioned rows within 20 km.
- Candidate Comm-B met/hazard channels checked in notebook: zero in this sample.

Interpretation:

- The pipeline works.
- The sample is high-altitude traffic, not low-level basin structure.
- This sample supports feasibility motivation, not cold-pool detection claims.

## Viability for Low-Level Cold-Pool Detection

Current viability is low with present evidence. The key missing piece is repeated low-level vertical sampling near basin floor/approach corridors during cold-pool periods.

Useful short-term rule: if a 30-60 day run still shows very low counts below roughly 7,000-9,000 ft MSL near KVEL-area distances, the project should pivot quickly toward UAT and/or improved receiver geometry instead of over-investing in unsupported derived variables.

## What ADS-B Can Still Deliver Now

Near-term value is real if scoped correctly:

- Coverage diagnostics by altitude, location, and time of day.
- Traffic-linked kinematic context and profile opportunity inventory.
- Field-yield evidence to decide which derived features are realistic.

High-impact next advice: treat Comm-B met fields as an empirical question, not an assumption. Publish non-null yield rates first, then pick features.

## Sampling Requirement

Longer targeted sampling is required.

1. Run at least 30-60 days continuous 1090 capture.
2. Add targeted KVEL arrival/departure windows and overnight cold-pool windows.
3. Preserve raw-message detail for selected validation windows.
4. Add UAT/978 capture if possible for likely low-level GA gains.
5. Evaluate second-receiver geometry to reduce low-level blind zones.

## Funding Readiness

Fundable framing: staged feasibility-to-validation, not finished detection product.

What is already persuasive:

- Working code and reproducible files.
- Real decoded observations.
- Explicit roadmap and hypotheses.

What must be demonstrated before stronger claims:

- Repeat low-level profile opportunity near basin floor.
- Measured Comm-B yield over longer windows.
- At least one anchored external validation case.

## Extensions to the Prelim Work (Next Batch)

Priority order is highest urgency first. Collaborators can append rows using this same format.

| Priority | Extension | Why now | Done if |
|---|---|---|---|
| 1 | Low-level sufficiency audit | No low-level evidence yet. | Counts by altitude, distance, and hour, plus pass/fail call. |
| 2 | Comm-B yield audit | Met/hazard yield is zero in sample. | Non-null rates for BDS 4,4 / 4,5 / 5,0 / 6,0. |
| 3 | KVEL targeted pilot (1-2 weeks) | Need real low-level hit rates. | Daily and window-level hit-rate summary with schedule advice. |
| 4 | Terrain-relative altitude proxy | MSL alone is weak in basin terrain. | Added proxy field with refreshed low-level maps/histograms. |
| 5 | Indicator false-positive test | Avoid noisy overclaims. | Trigger rates on control periods and keep/drop decisions. |
| 6 | One external validation case | Needed for scientific trust. | One aligned event brief versus station/reanalysis data. |
| 7 | Receiver-geometry limits memo | Blind spots may dominate conclusions. | Footprint map and short missing-zone note. |
| 8 | Open collaborator row policy | Prevents scope drift. | New rows include owner, date, and decision criterion. |

Execution rule for every row: include one concrete artifact (table/figure), then one short finding statement: supported, not supported, or inconclusive.

Two implementation notes:

- If row 1 and row 2 fail, do not expand feature engineering yet; expand sampling strategy first.
- For row 6, include uncertainty bounds in the case-study figure, not only a visual overlay.

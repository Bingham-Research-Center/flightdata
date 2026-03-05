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

| Pri | Extension | Output gate |
|---|---|---|
| 1 | Low-level sufficiency audit | Altitude-distance-hour counts with pass/fail call |
| 2 | Comm-B yield audit | Non-null rates for BDS 4,4 / 4,5 / 5,0 / 6,0 |
| 3 | KVEL targeted pilot (1-2 weeks) | Daily window hit-rate summary and schedule recommendation |
| 4 | Terrain-relative altitude proxy | Added proxy field plus refreshed low-level plots |
| 5 | False-positive check | Control-period trigger rates and keep/drop decision |
| 6 | External validation case | One aligned event brief versus reference data |
| 7 | Geometry limits memo | Footprint map and missing-zone summary |
| 8 | Open collaborator row policy | New rows include owner/date/decision rule |

Task notes:

1. If rows below roughly 7,000-9,000 ft MSL stay sparse near KVEL distances, pivot to sampling/geometry work first.
2. Treat Comm-B meteorology as measured yield, not assumed capability.
3. Capture windows should include local arrival/departure peaks and overnight cold-pool hours.
4. Keep AGL-proxy method transparent; document assumptions and terrain source.
5. Use control days explicitly to prevent optimistic indicator drift.
6. Include uncertainty bounds in validation figures, not only a visual match.
7. Use the geometry memo to prioritize receiver placement before scaling feature work.
8. Keep row updates brief so collaborators can scan and act quickly.

Execution rule for every row: include one concrete artifact (table/figure), then one short finding statement: supported, not supported, or inconclusive.

Two implementation notes:

- If row 1 and row 2 fail, do not expand feature engineering yet; expand sampling strategy first.
- For row 6, include uncertainty bounds in the case-study figure, not only a visual overlay.

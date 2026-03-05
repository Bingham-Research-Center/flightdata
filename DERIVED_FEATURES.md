# Derived Feature Research Plan (ADS-B / Comm-B)

## Scope & Assumptions
- Input is decoded messages with timestamps, position, velocity, and Comm-B fields when available.
- Aim: derive atmospheric/state features for a mountain basin, while keeping a compact, non‑redundant schema.
- Critical evidence status (March 2, 2026 sample): strong DF17 kinematics at cruise altitudes; no low-level rows in basin-relevant bands; no observed Comm-B met/hazard yield in that sample.

## Units & Conventions
- Define a **canonical unit system** (recommend SI) and convert at ingest.
- Preserve aviation‑native fields only when needed, with explicit suffixes (e.g., `_kt`, `_ft`, `_hpa`).
- Maintain a `units.md` table (column → unit) and use it as the single source of truth.

## Data Quality & Gating
- Require valid CRC, consistent even/odd position pair, and plausible ranges.
- Record per‑row quality flags (`pos_ok`, `vel_ok`, `bds44_ok`, etc.) and numeric uncertainty where available.
- Use short temporal windows to suppress spikes (median/Huber filters).
- Critical weakness: quality gating alone cannot recover missing low-level or missing Comm-B data; coverage sufficiency must be checked before feature claims.

---

## 1) Wind Vector at Aircraft Location
**Idea**: Estimate wind from airspeed + heading vs. ground speed + track.  
**Inputs**: ground speed/track, heading, TAS/IAS/Mach, altitude.  
**Plan**: convert to vectors, compute wind = ground − air; bin by altitude and time.  
**Hypothesis/Viability**: high if TAS/heading present; medium otherwise.  
**Notes**: fall back to multi‑aircraft consensus per bin.
- Evidence for viability (current): `velocity_gs`/`velocity_track` channels are populated in the sample and are usable for kinematic context.
- Evidence against / weakness (current): sample lacks IAS/TAS/Mach and low-level coverage, so basin-relevant wind inference is not yet demonstrated.

## 2) Thermodynamic State (T, p, ρ, θ, θe)
**Idea**: Derive density, potential temperature, virtual temperature.  
**Inputs**: temperature, pressure, humidity (BDS 4,4/4,5).  
**Plan**: compute θ, θv, ρ; aggregate by altitude/time.  
**Hypothesis/Viability**: moderate (depends on Comm‑B frequency).  
**Notes**: treat humidity as sparse; include missing‑aware features.
- Evidence for viability (current): decoder supports target Comm-B channels when present.
- Evidence against / weakness (current): March 2 sample has zero non-null BDS met/hazard variables, so thermodynamic viability is currently unproven.

## 3) Lapse Rate & Inversions
**Idea**: Estimate vertical temperature gradient to detect stability/inversions.  
**Inputs**: temp vs. altitude; time window.  
**Plan**: fit robust slope in altitude bins; flag inversion layers.  
**Hypothesis/Viability**: moderate; improved with multi‑aircraft binning.  
**Notes**: basin cold‑pool signals = strong low‑level inversions.
- Evidence for viability (current): altitude channels are present and support profile binning logic.
- Evidence against / weakness (current): no temperature channel and no low-level sample rows mean inversion detection is not yet supportable.

## 4) Turbulence & Shear Proxies
**Idea**: Use short‑window variance of vertical rate, roll, track jitter.  
**Inputs**: vertical rate, roll, track/heading, wind shear (BDS 4,5).  
**Plan**: compute rolling variance and exceedance flags.  
**Hypothesis/Viability**: high for relative changes; absolute severity medium.  
**Notes**: validate against BDS 4,5 when available.
- Evidence for viability (current): vertical-rate and track channels are populated enough for coarse relative-variability tests.
- Evidence against / weakness (current): roll/wind-shear/turbulence channels are absent in sample; severity interpretation is weak without those anchors.

## 5) Cold‑Air Pool Dynamics (Basin‑Scale)
**Idea**: Detect pooling, drainage, and breakup patterns.  
**Inputs**: near‑surface temps, wind vectors, stability indices.  
**Plan**: track nocturnal cooling rates, low‑level wind reversals, inversion depth.  
**Hypothesis/Viability**: high if low‑altitude traffic exists.  
**Notes**: emphasize temporal derivatives.
- Evidence for viability (current): concept aligns with project objective and available processing framework.
- Evidence against / weakness (current): current sample has no near-surface evidence, so basin cold-pool detection remains a hypothesis, not a demonstrated result.

## 6) Air‑Mass Change Detection
**Idea**: Identify regime shifts via multivariate change‑point detection.  
**Inputs**: wind, temp, pressure, humidity, turbulence proxies.  
**Plan**: segment time series; cluster states; compute transition likelihoods.  
**Hypothesis/Viability**: medium; improves with denser sampling.  
**Notes**: useful for ML priors and data QA.
- Evidence for viability (current): change-point methods can still be prototyped on available kinematic time series.
- Evidence against / weakness (current): missing thermodynamic channels and short windows risk false regime transitions and weak physical interpretability.

## 7) Boundary‑Layer Structure
**Idea**: Estimate mixed‑layer depth and entrainment.  
**Inputs**: temperature profiles, wind shear, turbulence proxies.  
**Plan**: detect gradients and turbulence peaks with altitude.  
**Hypothesis/Viability**: medium‑low; needs vertical coverage.  
**Notes**: combine multiple flights for composite profiles.
- Evidence for viability (current): methodology is standard if sufficient ascent/descent coverage is present.
- Evidence against / weakness (current): sample is dominated by high-altitude transit; boundary-layer structural inference is not currently evidenced.

## 8) Aircraft‑Derived Pressure Altitude Consistency
**Idea**: Use consistency between baro and geometric altitude as a QA signal.  
**Inputs**: altitude, baro pressure setting, position.  
**Plan**: compute residuals; flag outliers.  
**Hypothesis/Viability**: high; good for filtering.
- Evidence for viability (current): altitude and baro-setting related fields appear often enough for practical QA residual checks.
- Evidence against / weakness (current): QA residuals need independent references and broader flight-phase coverage to avoid overconfident filters.

---

## Schema Strategy (Non‑Redundant)
- **Raw‑core columns**: `timestamp`, `icao`, `df`, `typecode`, `latitude`, `longitude`, `altitude`, `velocity_gs`, `velocity_track`, `heading`, `ias/tas/mach` (when present).
- **Derived columns**: wind components, stability metrics, turbulence proxies, quality flags.
- **Do not duplicate**: keep only one of (ground vs. air) as source fields; store derived deltas instead.
- **Row identity**: keep `msg` or `msg_hash` during exploration; drop only after dedup is robust.
- **Outputs**: a “core” Parquet plus a “derived” Parquet joined by `(icao, timestamp, msg_hash)`.

## Experiment Phases
1) **Inventory**: quantify availability of Comm‑B and key fields.  
2) **Prototype**: compute wind + lapse‑rate + turbulence proxies.  
3) **Evaluate**: check spatial/temporal consistency; calibrate thresholds.  
4) **Optimize**: drop redundant columns, set final precision.  
5) **Productize**: stable schema + metadata/units table.

## UAT Exploration (New Hardware)
**Goal**: characterize what the new antenna/receivers unlock.  
**Plan**: compare message mix, low‑altitude coverage, DF 20/21 rates, and noise levels before/after.  
**Viability**: high; quick win and informs all downstream priorities.
- Evidence for viability (current): UAT is the most plausible near-term path to stronger low-level GA sampling.
- Evidence against / weakness (current): no in-repo UAT evidence yet; claims remain speculative until measured before/after comparisons are run.

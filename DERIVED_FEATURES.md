# Derived Feature Research Plan (ADS-B / Comm-B)

## Scope & Assumptions
- Input is decoded messages with timestamps, position, velocity, and Comm-B fields when available.
- Aim: derive atmospheric/state features for a mountain basin, while keeping a compact, non‑redundant schema.

## Units & Conventions
- Define a **canonical unit system** (recommend SI) and convert at ingest.
- Preserve aviation‑native fields only when needed, with explicit suffixes (e.g., `_kt`, `_ft`, `_hpa`).
- Maintain a `units.md` table (column → unit) and use it as the single source of truth.

## Data Quality & Gating
- Require valid CRC, consistent even/odd position pair, and plausible ranges.
- Record per‑row quality flags (`pos_ok`, `vel_ok`, `bds44_ok`, etc.) and numeric uncertainty where available.
- Use short temporal windows to suppress spikes (median/Huber filters).

---

## 1) Wind Vector at Aircraft Location
**Idea**: Estimate wind from airspeed + heading vs. ground speed + track.  
**Inputs**: ground speed/track, heading, TAS/IAS/Mach, altitude.  
**Plan**: convert to vectors, compute wind = ground − air; bin by altitude and time.  
**Hypothesis/Viability**: high if TAS/heading present; medium otherwise.  
**Notes**: fall back to multi‑aircraft consensus per bin.

## 2) Thermodynamic State (T, p, ρ, θ, θe)
**Idea**: Derive density, potential temperature, virtual temperature.  
**Inputs**: temperature, pressure, humidity (BDS 4,4/4,5).  
**Plan**: compute θ, θv, ρ; aggregate by altitude/time.  
**Hypothesis/Viability**: moderate (depends on Comm‑B frequency).  
**Notes**: treat humidity as sparse; include missing‑aware features.

## 3) Lapse Rate & Inversions
**Idea**: Estimate vertical temperature gradient to detect stability/inversions.  
**Inputs**: temp vs. altitude; time window.  
**Plan**: fit robust slope in altitude bins; flag inversion layers.  
**Hypothesis/Viability**: moderate; improved with multi‑aircraft binning.  
**Notes**: basin cold‑pool signals = strong low‑level inversions.

## 4) Turbulence & Shear Proxies
**Idea**: Use short‑window variance of vertical rate, roll, track jitter.  
**Inputs**: vertical rate, roll, track/heading, wind shear (BDS 4,5).  
**Plan**: compute rolling variance and exceedance flags.  
**Hypothesis/Viability**: high for relative changes; absolute severity medium.  
**Notes**: validate against BDS 4,5 when available.

## 5) Cold‑Air Pool Dynamics (Basin‑Scale)
**Idea**: Detect pooling, drainage, and breakup patterns.  
**Inputs**: near‑surface temps, wind vectors, stability indices.  
**Plan**: track nocturnal cooling rates, low‑level wind reversals, inversion depth.  
**Hypothesis/Viability**: high if low‑altitude traffic exists.  
**Notes**: emphasize temporal derivatives.

## 6) Air‑Mass Change Detection
**Idea**: Identify regime shifts via multivariate change‑point detection.  
**Inputs**: wind, temp, pressure, humidity, turbulence proxies.  
**Plan**: segment time series; cluster states; compute transition likelihoods.  
**Hypothesis/Viability**: medium; improves with denser sampling.  
**Notes**: useful for ML priors and data QA.

## 7) Boundary‑Layer Structure
**Idea**: Estimate mixed‑layer depth and entrainment.  
**Inputs**: temperature profiles, wind shear, turbulence proxies.  
**Plan**: detect gradients and turbulence peaks with altitude.  
**Hypothesis/Viability**: medium‑low; needs vertical coverage.  
**Notes**: combine multiple flights for composite profiles.

## 8) Aircraft‑Derived Pressure Altitude Consistency
**Idea**: Use consistency between baro and geometric altitude as a QA signal.  
**Inputs**: altitude, baro pressure setting, position.  
**Plan**: compute residuals; flag outliers.  
**Hypothesis/Viability**: high; good for filtering.

---

## Schema Strategy (Non‑Redundant)
- **Raw‑core columns**: `timestamp`, `icao`, `df`, `typecode`, `latitude`, `longitude`, `altitude`, `velocity_gs`, `velocity_track`, `heading`, `ias/tas/mach` (when present).
- **Derived columns**: wind components, stability metrics, turbulence proxies, quality flags.
- **Do not duplicate**: keep only one of (ground vs. air) as source fields; store derived deltas instead.
- **Row identity**: keep `msg` or `msg_hash` during exploration; drop only after dedup is robust.
- **Outputs**: a “core” Parquet plus a “derived” Parquet joined by `(icao, timestamp)`.

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

# Units Mapping (Column → Unit)

**Goal**: keep SI as default, label any aviation units explicitly.

| Column (or prefix) | Unit | Notes |
|---|---|---|
| `timestamp`, `datetime_utc` | seconds / UTC | epoch seconds + UTC datetime |
| `latitude`, `longitude` | degrees | WGS‑84 |
| `altitude` | ft | ADS‑B altitude is feet by convention |
| `selected_altitude_ft` | ft | from BDS 4,0 |
| `velocity_gs`, `airborne_speed`, `spdhdg_speed`, `gs50`, `tas50`, `ias60` | kt | ground/true/indicated |
| `velocity_track`, `airborne_heading`, `spdhdg_heading`, `trk50`, `hdg60` | degrees | 0–360 |
| `velocity_vr`, `airborne_vr`, `vr60_baro`, `vr60_ins` | ft/min | vertical rate |
| `mach60` | unitless | Mach number |
| `baro_pressure_setting`, `p44_hpa`, `p45_hpa` | hPa | pressure |
| `temp44_c`, `temp45_c` | °C | temperature |
| `hum44_pct`, `rh45_pct` | % | humidity |

If a derived feature is added, list it here with its unit.

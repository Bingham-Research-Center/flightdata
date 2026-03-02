````markdown
# ADS-B & Mode S Meteorological Decoder

This project decodes and processes ADS-B (DF17/18), Mode S Comm-B (DF20/21), and legacy Mode A/C (DF4/5) messages using [pyModeS](https://github.com/junzis/pyModeS).
It outputs three CSVs:

- **decoded_messages.csv**: Raw and cleaned fields, typed and split (no tuples), reduced precision.
- **derived_data.csv**: Message-level derived meteorological variables (wind, ISA deviation, etc.).
- **aggregated_summary.csv**: One-row-per-aircraft statistical summaries.

## Installation

```bash
pip install pandas numpy pyModeS
````

## Usage

```bash
python adsb_decoder_full.py --host <RECEIVER_HOST> --port <RECEIVER_PORT> --duration <SECONDS>
```

## Variables

| Column Name           | Unit           | Meaning                                    | Source / Method               | Notes / Warnings                                                               |
| --------------------- | -------------- | ------------------------------------------ | ----------------------------- | ------------------------------------------------------------------------------ |
| `icao`                | – (hex)        | Aircraft ICAO address                      | `pms.adsb.icao` or `pms.icao` | Unique per aircraft.                                                           |
| `datetime_utc`        | ISO datetime   | Timestamp of message reception             | System clock                  | Millisecond precision. Network/processing delays apply.                        |
| `timestamp`           | ms since epoch | Numeric timestamp                          | System clock                  | Rounded to ms.                                                                 |
| `typecode`            | int            | ADS-B type code for DF17/18                | `pms.adsb.typecode`           | 1–4 ID, 5–8 surface pos, 9–18 airborne pos, 19 vel, 28 status, 29 target state |
| `evensfc` / `odd_sfc` | –              | Raw ADS-B surface pos frames               | Internal cache                | Used for CPR decoding.                                                         |
| `even` / `odd`        | –              | Raw ADS-B airborne pos frames              | Internal cache                | Used for CPR decoding.                                                         |
| `ref_lat`, `ref_lon`  | degrees        | Receiver lat/lon for single-frame fallback | Constants in script           | Fallback position decode if no pair received.                                  |
|                       |                |                                            |                               |                                                                                |

|   |
| - |

|   |
| - |

| **Position**               |                  |                                                                       |                                                                |                                                                       |
| -------------------------- | ---------------- | --------------------------------------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------- |
| `latitude`, `longitude`    | degrees          | Aircraft position (WGS-84)                                            | `pms.adsb.airborne_position`, `..._surface_position`, fallback | Precision trimmed. Accuracy depends on NIC/NAC.                       |
| `altitude`                 | ft               | Barometric altitude (flight level)                                    | `pms.adsb.altitude`                                            | Pressure alt referenced to 1013.25 hPa. Requires ADS-B TC9–18 frames. |
| `alt_c`                    | ft               | Mode C transponder altitude                                           | `pms.common.altcode`                                           | Legacy SSR. 100 ft resolution.                                        |
| `altitude_diff`            | ft               | GNSS altitude – baro altitude                                         | ADS-B velocity message                                         | Indicates temperature/pressure deviations from ISA.                   |
| **Identification**         |                  |                                                                       |                                                                |                                                                       |
| `callsign`                 | –                | Flight call sign                                                      | `pms.adsb.callsign`, `pms.commb.cs20`                          | Airlines or tail number. Updates on ID messages only.                 |
| `category`                 | int              | Emitter category code                                                 | `pms.adsb.category`                                            | Aircraft type/size.                                                   |
| `squawk`                   | octal string     | SSR Mode A code (squawk)                                              | `pms.common.idcode`                                            | ATC-assigned. Not always broadcasted if ADS-B used.                   |
| **Velocity / Movement**    |                  |                                                                       |                                                                |                                                                       |
| `ground_speed`             | kt               | Horizontal speed                                                      | `pms.adsb.velocity` or `...airborne_velocity`                  | If `speed_type='GS'`, track-based; if `'AS'`, indicated airspeed.     |
| `track_angle`              | °                | Ground track or heading angle                                         | See above                                                      | ADS-B reports true degrees.                                           |
| `vertical_rate`            | ft/min           | Barometric climb (+) / descent (–) rate                               | ADS-B velocity                                                 |                                                                       |
| `speed_type`               | str              | Speed type flag (`GS` / `AS`)                                         | ADS-B velocity                                                 | GS = ground speed, AS = airspeed.                                     |
| **Emergency & Status**     |                  |                                                                       |                                                                |                                                                       |
| `emergency_state`          | int              | ADS-B emergency code                                                  | `pms.adsb.emergency_state`                                     | 1–7 various emergency types. Rare.                                    |
| `is_emergency`             | bool             | Emergency squawk active                                               | `pms.adsb.emergency_squawk`                                    |                                                                       |
| **Target State**           |                  |                                                                       |                                                                |                                                                       |
| `autopilot`                | bool             | Autopilot engaged                                                     | `pms.adsb.target_state`                                        |                                                                       |
| `lnav_mode`, `vnav_mode`   | bool             | Lateral / Vertical nav engaged                                        | Same as above                                                  |                                                                       |
| `approach_mode`            | bool             | Approach mode (localizer/glideslope) armed                            | Same as above                                                  |                                                                       |
| `alt_hold`                 | bool             | Altitude hold engaged                                                 | Same as above                                                  |                                                                       |
| `selected_altitude`        | ft               | Selected MCP/FCU altitude                                             | Same as above                                                  |                                                                       |
| `baro_setting`             | hPa              | Altimeter setting                                                     | Same as above                                                  | Sea-level pressure reference. May lag real QNH.                       |
| **Comm‑B / EHS**           |                  |                                                                       |                                                                |                                                                       |
| `ovc10`, `cap17`           | bool/int         | Comm-B overlay / capability flags                                     | `pms.commb.ovc10`, `pms.commb.cap17`                           | Not meteorological.                                                   |
| **BDS 4,0** (Mode S)       |                  |                                                                       |                                                                |                                                                       |
| `selalt_mcp`, `selalt_fms` | ft               | MCP / FMS selected altitude                                           | `pms.commb.selalt40mcp`, `pms.commb.selalt40fms`               |                                                                       |
| **BDS 4,4**                |                  | Meteorological routine air report                                     |                                                                |                                                                       |
| `wind_dir_reported`        | °                | Wind direction from instrument                                        | `pms.common.wind44`                                            | True degrees.                                                         |
| `wind_speed_reported`      | kt               | Wind speed from instrument                                            | Same                                                           |                                                                       |
| `temp_air`                 | °C               | Static air temperature                                                | `pms.common.temp44`                                            |                                                                       |
| `pressure`                 | hPa              | Static air pressure                                                   | `pms.common.p44`                                               |                                                                       |
| `humidity`                 | %                | Relative humidity                                                     | `pms.common.hum44`                                             |                                                                       |
| **BDS 4,5**                |                  | Meteorological hazard report                                          |                                                                |                                                                       |
| `turbulence`, `icing`,     | 0–3 scale        | Turbulence / icing / microburst / wind shear levels                   | `pms.common.mhr45`                                             | Categorical severity flags.                                           |
| **BDS 5,0**                |                  | Aircraft kinematic data                                               |                                                                |                                                                       |
| `roll`, `trk`, `gs`,       | – / kt / °       | Roll angle, track angle rate, GS, track rate, true airspeed           | `pms.commb.roll50`, `trk50`, `gs50`, `rtrk50`, `tas50`         | All optional. Some aircraft may not broadcast.                        |
| **BDS 6,0**                |                  | Additional kinematic / speed data                                     |                                                                |                                                                       |
| `heading_true`, `mach`     | ° / float        | True heading, Mach number                                             | `pms.commb.hdg60`, `pms.commb.mach60`                          |                                                                       |
| `ias`                      | kt               | Indicated airspeed                                                    | `pms.commb.ias60`                                              |                                                                       |
| `vr_baro`, `vr_ins`        | ft/min           | Baro / inertial vertical rate                                         | `pms.commb.vr60baro`, `pms.commb.vr60ins`                      |                                                                       |
| **Derived**                |                  |                                                                       |                                                                |                                                                       |
| `wind_u`, `wind_v`         | m/s              | Wind vector components (east, north)                                  | Computed from heading, track, speed                            | Uses GS as TAS proxy if true airspeed missing.                        |
| `wind_speed`, `wind_dir`   | kt / °           | Wind magnitude & direction                                            | From `wind_u`, `wind_v`                                        |                                                                       |
| `isa_dev`                  | °C               | Estimated ISA temperature deviation                                   | Derived from Mach and baro alt                                 | Relies on speed/temperature formulas; flag if error >2°C.             |
| **Aggregation**            |                  |                                                                       |                                                                |                                                                       |
| Various summary stats      | – / ft / kt / °C | avg\_altitude, alt\_trend, avg\_mach, avg\_wind\_speed, avg\_isa\_dev | Grouped by `icao`                                              | Use summary for quick basin-scale met analysis.                       |

**Warnings:**

- Check NIC/NAC (`nac_p`, `nac_v`) before trusting position/velocity accuracy.
- Derived wind/temperature have assumptions; use direct reports if available.
- Mode S BDS registers depend on ground interrogations; may be sparse.

```
```

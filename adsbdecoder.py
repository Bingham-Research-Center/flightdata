import argparse
import hashlib
import signal
from collections import defaultdict
from datetime import datetime, timezone

import polars as pl
import pyModeS as pms
from pyModeS.extra.tcpclient import TcpClient

DEFAULT_HOST = "129.123.91.145"
DEFAULT_PORT = 30005
DEFAULT_REF_LAT = 40.46014413068818
DEFAULT_REF_LON = -109.56578602889579
DEFAULT_CAPTURE_SECONDS = 15

# Build function dictionaries more comprehensively
ADSB_FUNCS = {
    # Basic info
    "callsign": pms.adsb.callsign,
    "category": pms.adsb.category,
    # Position
    "altitude": pms.adsb.altitude,
    "oe_flag": pms.adsb.oe_flag,
    # Velocity
    "velocity": pms.adsb.velocity,
    "speed_heading": pms.adsb.speed_heading,
    "airborne_velocity": pms.adsb.airborne_velocity,
    "altitude_diff": pms.adsb.altitude_diff,
    # Uncertainty/accuracy
    "version": pms.adsb.version,
    "nuc_p": pms.adsb.nuc_p,
    "nuc_v": pms.adsb.nuc_v,
    "nac_p": pms.adsb.nac_p,
    "nac_v": pms.adsb.nac_v,
    "nic_s": pms.adsb.nic_s,
    "nic_a_c": pms.adsb.nic_a_c,
    "nic_b": pms.adsb.nic_b,
    "sil": pms.adsb.sil,
    # Target state (TC=29)
    "selected_altitude": pms.adsb.selected_altitude,
    "selected_heading": pms.adsb.selected_heading,
    "baro_pressure_setting": pms.adsb.baro_pressure_setting,
    "autopilot": pms.adsb.autopilot,
    "vnav_mode": pms.adsb.vnav_mode,
    "altitude_hold_mode": pms.adsb.altitude_hold_mode,
    "approach_mode": pms.adsb.approach_mode,
    "tcas_operational": pms.adsb.tcas_operational,
    "lnav_mode": pms.adsb.lnav_mode,
    # Emergency
    "emergency_state": pms.adsb.emergency_state,
    "emergency_squawk": pms.adsb.emergency_squawk,
    "is_emergency": pms.adsb.is_emergency,
}

# BDS flags
BDS_FLAGS = {
    "bds10": pms.bds.bds10,
    "bds17": pms.bds.bds17,
    "bds20": pms.bds.bds20,
    "bds30": pms.bds.bds30,
    "bds40": pms.bds.bds40,
    "bds44": pms.bds.bds44,
    "bds45": pms.bds.bds45,
    "bds50": pms.bds.bds50,
    "bds60": pms.bds.bds60,
}

# Comm-B decoders
COMMB_FUNCS = {
    # BDS 1,0 - Data link capability
    "ovc10": pms.commb.ovc10,
    # BDS 1,7 - GICB capability
    "cap17": pms.commb.cap17,
    # BDS 2,0 - Aircraft ID
    "cs20": pms.commb.cs20,
    # BDS 4,0 - Selected vertical intention
    "selalt40_mcp": pms.commb.selalt40mcp,
    "selalt40_fms": pms.commb.selalt40fms,
    "p40_baro": pms.commb.p40baro,
    # BDS 4,4 - Meteorological routine
    "wind44": pms.commb.wind44,
    "temp44": pms.commb.temp44,
    "p44": pms.commb.p44,
    "hum44": pms.commb.hum44,
    # BDS 4,5 - Meteorological hazard
    "turb45": pms.commb.turb45,
    "ws45": pms.commb.ws45,
    "mb45": pms.commb.mb45,
    "ic45": pms.commb.ic45,
    "wv45": pms.commb.wv45,
    "temp45": pms.commb.temp45,
    "p45": pms.commb.p45,
    "rh45": pms.commb.rh45,
    # BDS 5,0 - Track and turn
    "roll50": pms.commb.roll50,
    "trk50": pms.commb.trk50,
    "gs50": pms.commb.gs50,
    "rtrk50": pms.commb.rtrk50,
    "tas50": pms.commb.tas50,
    # BDS 6,0 - Heading and speed
    "hdg60": pms.commb.hdg60,
    "ias60": pms.commb.ias60,
    "mach60": pms.commb.mach60,
    "vr60_baro": pms.commb.vr60baro,
    "vr60_ins": pms.commb.vr60ins,
}

TUPLE_FIELD_MAP = {
    "velocity": ("velocity_gs", "velocity_track", "velocity_vr", "velocity_type"),
    "speed_heading": ("spdhdg_speed", "spdhdg_heading"),
    "airborne_velocity": (
        "airborne_speed",
        "airborne_heading",
        "airborne_vr",
        "airborne_type",
    ),
    "selected_altitude": ("selected_altitude_ft", "selected_altitude_src"),
    "wind44": ("wind44_speed", "wind44_dir"),
    "temp44": ("temp44_c",),
    "p44": ("p44_hpa",),
    "hum44": ("hum44_pct",),
    "temp45": ("temp45_c",),
    "p45": ("p45_hpa",),
    "rh45": ("rh45_pct",),
}

STEP_QUANTIZATION = [
    (("altitude", "selected_altitude_ft", "altitude_diff"), 25.0),
    (("vr", "vertical_rate"), 10.0),
]

DECIMAL_QUANTIZATION = [
    (("latitude", "longitude"), 4),
    (("heading", "track", "dir"), 1),
    (("speed", "gs", "tas", "ias"), 1),
    (("roll",), 1),
    (("mach",), 3),
    (("temp",), 1),
    (("pressure", "p44_hpa", "p45_hpa", "baro_pressure_setting"), 1),
    (("hum", "rh"), 0),
]

CORE_COLUMNS = [
    "timestamp",
    "datetime_utc",
    "icao",
    "df",
    "typecode",
    "msg_hash",
    "latitude",
    "longitude",
    "position_type",
    "altitude",
    "selected_altitude_ft",
    "velocity_gs",
    "velocity_track",
    "velocity_vr",
    "velocity_type",
    "airborne_speed",
    "airborne_heading",
    "airborne_vr",
    "airborne_type",
    "spdhdg_speed",
    "spdhdg_heading",
    "baro_pressure_setting",
    "callsign",
    "category",
]

KEY_COLUMNS = ["timestamp", "datetime_utc", "icao", "msg_hash"]


class TimeoutException(Exception):
    """Raised when capture timeout is reached."""


def _alarm_handler(signum, frame):
    raise TimeoutException()


def _to_datetime(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _safe_decode(func, msg):
    try:
        return func(msg)
    except Exception:
        return None


def _flatten_record(rec):
    flat = {}
    for key, val in rec.items():
        if isinstance(val, (tuple, list)):
            names = TUPLE_FIELD_MAP.get(key)
            if names:
                for idx, name in enumerate(names):
                    if idx < len(val):
                        flat[name] = val[idx]
                if len(val) > len(names):
                    for idx in range(len(names), len(val)):
                        flat[f"{key}_{idx}"] = val[idx]
            else:
                for idx, item in enumerate(val):
                    flat[f"{key}_{idx}"] = item
        else:
            flat[key] = val
    return flat


def _apply_quantization(df):
    exprs = []
    for col, dtype in df.schema.items():
        if not dtype.is_numeric():
            continue

        quantized = False
        for substrings, step in STEP_QUANTIZATION:
            if any(sub in col for sub in substrings):
                exprs.append(((pl.col(col) / step).round(0) * step).alias(col))
                quantized = True
                break

        if quantized:
            continue

        for substrings, decimals in DECIMAL_QUANTIZATION:
            if any(sub in col for sub in substrings):
                exprs.append(pl.col(col).round(decimals).alias(col))
                break

    if exprs:
        return df.with_columns(exprs)
    return df


def _prepare_output_frames(records):
    data_df = pl.DataFrame([_flatten_record(rec) for rec in records])
    if data_df.height == 0:
        return data_df, data_df, data_df

    sort_cols = [c for c in ["icao", "datetime_utc"] if c in data_df.columns]
    if sort_cols:
        data_df = data_df.sort(sort_cols)

    data_df = _apply_quantization(data_df)

    core_cols = [c for c in CORE_COLUMNS if c in data_df.columns]
    key_cols = [c for c in KEY_COLUMNS if c in data_df.columns]

    core_df = data_df.select(core_cols) if core_cols else data_df
    derived_cols = [c for c in data_df.columns if c not in set(core_cols)]
    derived_select_cols = list(dict.fromkeys(key_cols + derived_cols))
    derived_df = data_df.select(derived_select_cols) if derived_select_cols else data_df

    return data_df, core_df, derived_df


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Capture and decode ADS-B/Comm-B messages from a Beast feed."
    )
    parser.add_argument("--host", default=DEFAULT_HOST, help="Beast receiver host.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Beast receiver TCP port.")
    parser.add_argument(
        "--ref-lat",
        type=float,
        default=DEFAULT_REF_LAT,
        help="Reference latitude for position decoding.",
    )
    parser.add_argument(
        "--ref-lon",
        type=float,
        default=DEFAULT_REF_LON,
        help="Reference longitude for position decoding.",
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=DEFAULT_CAPTURE_SECONDS,
        help="Capture duration in seconds.",
    )
    parser.add_argument(
        "--core-out",
        default="adsb_core.parquet",
        help="Output path for core parquet file.",
    )
    parser.add_argument(
        "--derived-out",
        default="adsb_derived.parquet",
        help="Output path for derived parquet file.",
    )
    args = parser.parse_args()
    if args.seconds < 1:
        raise SystemExit("--seconds must be >= 1")
    return args


class BeastDF(TcpClient):
    def __init__(self, host, port, ref_lat=None, ref_lon=None):
        super().__init__(host, port, "beast")
        self.records = []
        self.position_cache = {}
        self.msg_counts = defaultdict(int)
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon

    @property
    def has_ref_position(self):
        return self.ref_lat is not None and self.ref_lon is not None

    def handle_messages(self, messages):
        for raw_bytes, ts in messages:
            msg = self._normalize_message(raw_bytes)
            if msg is None:
                self.msg_counts["len_fail"] += 1
                continue

            if pms.crc(msg) != 0:
                self.msg_counts["crc_fail"] += 1
                continue

            df = pms.df(msg)
            icao = pms.icao(msg)
            if not icao:
                continue

            self.msg_counts[f"df{df}"] += 1
            rec = self._base_record(ts, msg, df, icao)

            if df in [17, 18]:
                self._decode_adsb(msg, ts, icao, rec)
            elif df in [20, 21]:
                self._decode_commb(msg, rec)
            elif df in [4, 5]:
                self._decode_surveillance_altitude(msg, rec)
            elif df == 11:
                self._decode_all_call(msg, rec)

            self.records.append(rec)

    def _normalize_message(self, raw_bytes):
        if isinstance(raw_bytes, (bytes, bytearray)):
            msg = raw_bytes.hex()
        else:
            msg = str(raw_bytes).strip()

        if len(msg) != 28:
            return None
        return msg

    def _base_record(self, ts, msg, df, icao):
        return {
            "timestamp": ts,
            "datetime_utc": _to_datetime(ts),
            "msg": msg,
            "msg_hash": hashlib.blake2s(msg.encode("utf-8"), digest_size=8).hexdigest(),
            "df": df,
            "icao": icao,
        }

    def _decode_adsb(self, msg, ts, icao, rec):
        tc = _safe_decode(pms.adsb.typecode, msg)
        if tc is None:
            return

        rec["typecode"] = tc
        self.msg_counts[f"tc{tc}"] += 1

        for field_name, func in ADSB_FUNCS.items():
            val = _safe_decode(func, msg)
            if val is not None and val != (None, None):
                rec[field_name] = val

        if tc in range(5, 23):
            self._handle_position_message(msg, ts, icao, tc, rec)

    def _decode_commb(self, msg, rec):
        bds_code = _safe_decode(lambda m: pms.bds.infer(m, mrar=True), msg)
        rec["bds"] = bds_code
        if bds_code:
            self.msg_counts[f"bds{bds_code}"] += 1

        for bds_name, module in BDS_FLAGS.items():
            fn_name = f"is{bds_name[3:]}"
            if hasattr(module, fn_name):
                fn = getattr(module, fn_name)
                rec[fn_name] = _safe_decode(fn, msg)

        for key, func in COMMB_FUNCS.items():
            val = _safe_decode(func, msg)
            if val is not None:
                rec[key] = val

    def _decode_surveillance_altitude(self, msg, rec):
        altitude = _safe_decode(pms.common.altcode, msg)
        if altitude is not None:
            rec["altitude"] = altitude

    def _decode_all_call(self, msg, rec):
        capability = _safe_decode(pms.common.ca, msg)
        if capability is not None:
            rec["capability"] = capability

    def _handle_position_message(self, msg, ts, icao, tc, rec):
        oe_flag = _safe_decode(pms.adsb.oe_flag, msg)
        if oe_flag is None:
            return

        rec["oe_flag"] = oe_flag

        if icao not in self.position_cache:
            self.position_cache[icao] = {}

        if oe_flag == 0:
            self.position_cache[icao]["even"] = (msg, ts)
        else:
            self.position_cache[icao]["odd"] = (msg, ts)

        if "even" not in self.position_cache[icao] or "odd" not in self.position_cache[icao]:
            return

        even_msg, even_ts = self.position_cache[icao]["even"]
        odd_msg, odd_ts = self.position_cache[icao]["odd"]
        if abs(even_ts - odd_ts) >= 10:
            return

        try:
            if 5 <= tc <= 8:
                if self.has_ref_position:
                    lat, lon = pms.adsb.surface_position(
                        even_msg,
                        odd_msg,
                        even_ts,
                        odd_ts,
                        self.ref_lat,
                        self.ref_lon,
                    )
                    rec["latitude"] = lat
                    rec["longitude"] = lon
                    rec["position_type"] = "surface"
            else:
                lat, lon = pms.adsb.airborne_position(even_msg, odd_msg, even_ts, odd_ts)
                rec["latitude"] = lat
                rec["longitude"] = lon
                rec["position_type"] = "airborne"
        except Exception:
            if self.has_ref_position:
                ref_pos = _safe_decode(
                    lambda m: pms.adsb.position_with_ref(m, self.ref_lat, self.ref_lon),
                    msg,
                )
                if ref_pos is not None:
                    lat, lon = ref_pos
                    rec["latitude"] = lat
                    rec["longitude"] = lon
                    rec["position_type"] = "with_ref"

    def get_statistics(self):
        return dict(self.msg_counts)


def main():
    args = _parse_args()
    client = BeastDF(args.host, args.port, args.ref_lat, args.ref_lon)

    signal.signal(signal.SIGALRM, _alarm_handler)
    signal.alarm(args.seconds)

    try:
        client.run()
    except TimeoutException:
        print(f"\\n{args.seconds} seconds elapsed, stopping capture.")
    finally:
        signal.alarm(0)

    print("\\nMessage Statistics:")
    for key, value in sorted(client.get_statistics().items()):
        print(f"  {key}: {value}")

    data_df, core_df, derived_df = _prepare_output_frames(client.records)
    if data_df.height == 0:
        print("\\nNo valid records captured.")
        print("Hint: check host/port connectivity, receiver availability, and capture length.")
        return

    core_df.write_parquet(args.core_out, compression="zstd")
    derived_df.write_parquet(args.derived_out, compression="zstd")

    total_records = data_df.height
    unique_aircraft = (
        data_df.select(pl.col("icao").n_unique()).item() if "icao" in data_df.columns else 0
    )
    print(f"\\nTotal records: {total_records}")
    print(f"Unique aircraft: {unique_aircraft}")

    if "latitude" in data_df.columns:
        pos_success = data_df.select(pl.col("latitude").is_not_null().sum()).item()
        pct = (pos_success / total_records) * 100 if total_records else 0.0
        print(f"Successful position decodes: {pos_success}/{total_records} ({pct:.1f}%)")


if __name__ == "__main__":
    main()

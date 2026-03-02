'''
adsbdecodermain.py

Full ADS-B & Mode S Meteorological Decoder

Decodes ADS-B (DF17/18), Mode S Comm-B (DF20/21), and legacy Mode A/C (DF4/5) messages via pyModeS.
Extracts raw fields, splits tuple outputs into typed columns, removes redundancies, and computes derived meteorological variables.
Produces three Parquet files:
  - decoded_messages.parquet
  - derived_data.parquet
  - aggregated_summary.parquet

Usage:
  python adsbdecodermain.py --host <RECEIVER_HOST> --port <RECEIVER_PORT> --duration <SECONDS>
'''

import argparse
import socket
import time
import pandas as pd
import numpy as np
import pyModeS as pms

# Receiver fallback coordinates (set your receiver's lat/lon)
RECEIVER_LAT = 40.00
RECEIVER_LON = -105.00


def receive_messages(host: str, port: int, duration: float):
    end_time = time.time() + duration
    with socket.create_connection((host, port)) as sock:
        f = sock.makefile('rb')
        while time.time() < end_time:
            raw = f.readline()
            print(f"RAW LINE: {raw!r}")        # see if anything comes over TCP
            if not raw:
                continue
            # try:
            line = raw.decode('ascii', 'ignore').strip()
            print(f"PARSED LINE: {line}")     # check your SBS text format
            msg = line.split(',')[-1]
            print(f"MSG: {msg} (len={len(msg)})")  # confirm length before decode_record
            yield msg, time.time()
            # except Exception:
            #     continue


def decode_record(msg: str, ts: float) -> dict | None:
    print(f"DECODING: {msg} → len={len(msg)}, crc={pms.crc(msg)}")
    if len(msg) != 28 or pms.crc(msg) != 0:
        print("→ dropped by length/CRC filter")
        return None
    rec: dict = {}
    rec['timestamp'] = ts
    # Always extract ICAO
    rec['icao'] = msg[2:8]
    df = pms.df(msg)

    # ADS-B (DF 17/18)
    if df in (17, 18):
        tc = pms.adsb.typecode(msg)
        rec['typecode'] = int(tc)
        # Identification
        if 1 <= tc <= 4:
            rec['callsign'] = pms.adsb.callsign(msg)
            rec['category'] = pms.adsb.category(msg)
        # Surface position (TC 5-8)
        if 5 <= tc <= 8:
            try:
                lat, lon = pms.adsb.surface_position(
                    msg,
                    rec.get('evensfc'), rec.get('odd_sfc'),
                    RECEIVER_LAT, RECEIVER_LON)
                rec['latitude'], rec['longitude'] = float(lat), float(lon)
            except Exception:
                pass
            # cache for pairing
            if tc % 2 == 0:
                rec['evensfc'] = msg
            else:
                rec['odd_sfc'] = msg
        # Airborne position (TC 9-18)
        if 9 <= tc <= 18:
            try:
                lat, lon = pms.adsb.airborne_position(
                    msg,
                    rec.get('even'), rec.get('odd'),
                    RECEIVER_LAT, RECEIVER_LON)
                rec['latitude'], rec['longitude'] = float(lat), float(lon)
            except Exception:
                pass
            if tc % 2 == 0:
                rec['even'] = msg
            else:
                rec['odd'] = msg
        # Fallback single-frame position
        if 'latitude' not in rec:
            try:
                lat, lon = pms.adsb.airborne_position_with_ref(
                    msg, RECEIVER_LAT, RECEIVER_LON)
                rec['latitude'], rec['longitude'] = float(lat), float(lon)
                rec['pos_type'] = 'with_ref'
            except Exception:
                pass
        # Altitude
        try:
            rec['altitude'] = int(pms.adsb.altitude(msg))
        except Exception:
            pass
        # Velocity (TC 19)
        if tc == 19:
            try:
                gs, track, vr, st = pms.adsb.velocity(msg)
            except Exception:
                gs, track, vr, st = pms.adsb.airborne_velocity(msg)
            rec['ground_speed'] = int(gs)
            rec['track_angle'] = float(track)
            rec['vertical_rate'] = int(vr)
            rec['speed_type'] = st
            # GNSS vs Baro altitude difference
            try:
                rec['altitude_diff'] = int(pms.adsb.adsb_velocity(msg)[4])
            except Exception:
                pass
        # Emergency & status (TC 28)
        if tc == 28:
            rec['emergency_state'] = pms.adsb.emergency_state(msg)
            rec['is_emergency'] = pms.adsb.emergency_squawk(msg)
        # Target state (TC 29)
        if tc == 29:
            s = pms.adsb.target_state(msg)
            keys = [
                'autopilot','lnav_mode','vnav_mode','approach_mode',
                'alt_hold','selected_altitude','baro_setting'
            ]
            for k, v in zip(keys, s):
                rec[k] = v

    # Legacy Mode C altitude DF4/20
    elif df in (4, 20):
        try:
            rec['alt_c'] = int(pms.common.altcode(msg))
        except Exception:
            pass
    # Legacy Mode A squawk DF5/21
    elif df in (5, 21):
        try:
            rec['squawk'] = pms.common.idcode(msg)
        except Exception:
            pass

    # Comm-B / EHS (DF20/21)
    if df in (20, 21):
        # Overlay / capabilities
        for fn, name in [(pms.commb.ovc10,'ovc10'), (pms.commb.cap17,'cap17')]:
            try:
                rec[name] = fn(msg)
            except Exception:
                pass
        try:
            rec['callsign_bds20'] = pms.commb.cs20(msg)
        except Exception:
            pass
        # BDS 4,0 selected & baro
        try:
            rec['selalt_mcp'] = pms.commb.selalt40mcp(msg)
            rec['selalt_fms'] = pms.commb.selalt40fms(msg)
            rec['baro_setting'] = pms.commb.p40baro(msg)
        except Exception:
            pass
        # BDS 4,4 meteorological report
        try:
            wdir, wspd = pms.common.wind44(msg)
            rec['wind_dir_reported'] = float(wdir)
            rec['wind_speed_reported'] = float(wspd)
            rec['temp_air'] = pms.common.temp44(msg)
            rec['pressure'] = pms.common.p44(msg)
            rec['humidity'] = pms.common.hum44(msg)
        except Exception:
            pass
        # BDS 4,5 hazard report
        try:
            rec['turbulence'], rec['icing'], rec['microburst'], rec['wind_shear'] = pms.common.mhr45(msg)
        except Exception:
            pass
        # BDS 5,0 kinematics
        for fn, name in [
            (pms.commb.roll50,'roll'), (pms.commb.trk50,'trk'),
            (pms.commb.gs50,'gs'), (pms.commb.rtrk50,'rtrk'),
            (pms.commb.tas50,'tas')
        ]:
            try:
                rec[name] = fn(msg)
            except Exception:
                pass
        # BDS 6,0 heading/airspeed
        try:
            hdg, mach = pms.commb.hdg60(msg)
            rec['heading_true'] = hdg
            rec['mach'] = mach
        except Exception:
            pass
        try:
            rec['ias'] = pms.commb.ias60(msg)
        except Exception:
            pass
        try:
            rec['vr_baro'] = pms.commb.vr60baro(msg)
            rec['vr_ins'] = pms.commb.vr60ins(msg)
        except Exception:
            pass

    # Final ISO timestamp
    rec['datetime_utc'] = pd.to_datetime(
        rec['timestamp'], unit='s').strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
    return rec


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = df.drop(columns=['df'], errors='ignore')
    df = df.drop_duplicates(subset=['icao','timestamp','ground_speed','track_angle','vertical_rate'])
    df['icao'] = df['icao'].astype('category')
    if 'callsign' in df.columns:
        df['callsign'] = df['callsign'].astype('category')
    # Cast numeric columns
    for col, dtype in [
        ('ground_speed','Int16'), ('track_angle','float32'),
        ('vertical_rate','Int16'), ('altitude','Int32'),
        ('altitude_diff','Int32'), ('selected_altitude','Int32')
    ]:
        if col in df.columns:
            df[col] = df[col].astype(dtype)
    # Reduce timestamp precision
    df['timestamp'] = (df['timestamp'] * 1000).round().astype('Int64')
    return df.sort_values(['icao','timestamp'])


def derive_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    # Compute wind components
    def wind_uv(row):
        if pd.notna(row.get('heading_true')) and pd.notna(row.get('ground_speed')):
            hdg = np.deg2rad(row['heading_true'])
            trk = np.deg2rad(row['track_angle'])
            tas = row['ground_speed'] * 0.514444
            u = tas * np.cos(hdg) - tas * np.cos(trk)
            v = tas * np.sin(hdg) - tas * np.sin(trk)
            return pd.Series({'wind_u':u,'wind_v':v})
        return pd.Series({'wind_u':np.nan,'wind_v':np.nan})
    uv = d.apply(wind_uv, axis=1)
    d['wind_u'] = uv['wind_u']
    d['wind_v'] = uv['wind_v']
    d['wind_speed'] = np.hypot(d['wind_u'], d['wind_v']).astype('float32')
    d['wind_dir'] = (np.degrees(np.arctan2(-d['wind_u'], -d['wind_v'])) % 360).astype('float32')
    # Estimate ISA deviation
    def isa_dev(row):
        if pd.notna(row.get('mach')) and pd.notna(row.get('altitude')):
            alt_m = row['altitude'] * 0.3048
            isa_t = 288.15 - 0.0065 * alt_m
            a = (row['ground_speed'] * 0.514444) / row['mach']
            T = a**2 / (1.4 * 287.05)
            return float(T - isa_t)
        return np.nan
    d['isa_dev'] = d.apply(isa_dev, axis=1).astype('float32')
    return d


def aggregate_summary(df: pd.DataFrame, d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby('icao')
    summary = g.agg(
        callsign=('callsign','first'),
        avg_altitude=('altitude','mean'),
        start_altitude=('altitude','first'),
        end_altitude=('altitude','last'),
        avg_mach=('mach','mean'),
        avg_wind_speed=('wind_speed','mean'),
        avg_isa_dev=('isa_dev','mean')
    )
    # Compute altitude trend (ft/min)
    t = (df.groupby('icao')['timestamp'].max() - df.groupby('icao')['timestamp'].min()) / 60000
    summary['alt_trend'] = (summary['end_altitude'] - summary['start_altitude']) / t
    return summary.reset_index()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--duration', type=float, default=60)
    args = parser.parse_args()

    records = []
    for msg, ts in receive_messages(args.host, args.port, args.duration):
        rec = decode_record(msg, ts)
        if rec is not None:
            records.append(rec)

    df_raw = pd.DataFrame(records)

    if df_raw.empty:
        print("⚠️  No ADS-B messages decoded in that interval. Exiting.")
        return

    df_clean = process_dataframe(df_raw)
    df_derived = derive_dataframe(df_clean)
    df_summary = aggregate_summary(df_clean, df_derived)

    df_clean.to_parquet('decoded_messages.parquet', index=False)
    df_derived.to_parquet('derived_data.parquet', index=False)
    df_summary.to_parquet('aggregated_summary.parquet', index=False)


if __name__ == '__main__':
    main()

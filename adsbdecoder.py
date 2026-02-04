import hashlib
import signal
from collections import defaultdict
from datetime import datetime, timezone

import pyModeS as pms
from pyModeS.extra.tcpclient import TcpClient
import polars as pl

class TimeoutException(Exception):
    pass

def _alarm_handler(signum, frame):
    raise TimeoutException()

# Build function dictionaries more comprehensively
ADSB_FUNCS = {
    # Basic info
    'callsign': pms.adsb.callsign,
    'category': pms.adsb.category,
    
    # Position
    'altitude': pms.adsb.altitude,
    'oe_flag': pms.adsb.oe_flag,
    
    # Velocity
    'velocity': pms.adsb.velocity,
    'speed_heading': pms.adsb.speed_heading,
    'airborne_velocity': pms.adsb.airborne_velocity,
    'altitude_diff': pms.adsb.altitude_diff,
    
    # Uncertainty/accuracy
    'version': pms.adsb.version,
    'nuc_p': pms.adsb.nuc_p,
    'nuc_v': pms.adsb.nuc_v,
    'nac_p': pms.adsb.nac_p,
    'nac_v': pms.adsb.nac_v,
    'nic_s': pms.adsb.nic_s,
    'nic_a_c': pms.adsb.nic_a_c,
    'nic_b': pms.adsb.nic_b,
    'sil': pms.adsb.sil,
    
    # Target state (TC=29)
    'selected_altitude': pms.adsb.selected_altitude,
    'selected_heading': pms.adsb.selected_heading,
    'baro_pressure_setting': pms.adsb.baro_pressure_setting,
    'autopilot': pms.adsb.autopilot,
    'vnav_mode': pms.adsb.vnav_mode,
    'altitude_hold_mode': pms.adsb.altitude_hold_mode,
    'approach_mode': pms.adsb.approach_mode,
    'tcas_operational': pms.adsb.tcas_operational,
    'lnav_mode': pms.adsb.lnav_mode,
    
    # Emergency
    'emergency_state': pms.adsb.emergency_state,
    'emergency_squawk': pms.adsb.emergency_squawk,
    'is_emergency': pms.adsb.is_emergency,
}

# BDS flags
BDS_FLAGS = {
    'bds10': pms.bds.bds10,
    'bds17': pms.bds.bds17,
    'bds20': pms.bds.bds20,
    'bds30': pms.bds.bds30,
    'bds40': pms.bds.bds40,
    'bds44': pms.bds.bds44,
    'bds45': pms.bds.bds45,
    'bds50': pms.bds.bds50,
    'bds60': pms.bds.bds60,
}

# Comm-B decoders
COMMB_FUNCS = {
    # BDS 1,0 - Data link capability
    'ovc10': pms.commb.ovc10,
    
    # BDS 1,7 - GICB capability
    'cap17': pms.commb.cap17,
    
    # BDS 2,0 - Aircraft ID
    'cs20': pms.commb.cs20,
    
    # BDS 4,0 - Selected vertical intention
    'selalt40_mcp': pms.commb.selalt40mcp,
    'selalt40_fms': pms.commb.selalt40fms,
    'p40_baro': pms.commb.p40baro,
    
    # BDS 4,4 - Meteorological routine
    'wind44': pms.commb.wind44,
    'temp44': pms.commb.temp44,
    'p44': pms.commb.p44,
    'hum44': pms.commb.hum44,
    
    # BDS 4,5 - Meteorological hazard
    'turb45': pms.commb.turb45,
    'ws45': pms.commb.ws45,
    'mb45': pms.commb.mb45,
    'ic45': pms.commb.ic45,
    'wv45': pms.commb.wv45,
    'temp45': pms.commb.temp45,
    'p45': pms.commb.p45,
    'rh45': pms.commb.rh45,
    
    # BDS 5,0 - Track and turn
    'roll50': pms.commb.roll50,
    'trk50': pms.commb.trk50,
    'gs50': pms.commb.gs50,
    'rtrk50': pms.commb.rtrk50,
    'tas50': pms.commb.tas50,
    
    # BDS 6,0 - Heading and speed
    'hdg60': pms.commb.hdg60,
    'ias60': pms.commb.ias60,
    'mach60': pms.commb.mach60,
    'vr60_baro': pms.commb.vr60baro,
    'vr60_ins': pms.commb.vr60ins,
}

TUPLE_FIELD_MAP = {
    'velocity': ('velocity_gs', 'velocity_track', 'velocity_vr', 'velocity_type'),
    'speed_heading': ('spdhdg_speed', 'spdhdg_heading'),
    'airborne_velocity': ('airborne_speed', 'airborne_heading', 'airborne_vr', 'airborne_type'),
    'selected_altitude': ('selected_altitude_ft', 'selected_altitude_src'),
    'wind44': ('wind44_speed', 'wind44_dir'),
    'temp44': ('temp44_c',),
    'p44': ('p44_hpa',),
    'hum44': ('hum44_pct',),
    'temp45': ('temp45_c',),
    'p45': ('p45_hpa',),
    'rh45': ('rh45_pct',),
}

STEP_QUANTIZATION = [
    (('altitude', 'selected_altitude_ft', 'altitude_diff'), 25.0),
    (('vr', 'vertical_rate'), 10.0),
]

DECIMAL_QUANTIZATION = [
    (('latitude', 'longitude'), 4),
    (('heading', 'track', 'dir'), 1),
    (('speed', 'gs', 'tas', 'ias'), 1),
    (('roll',), 1),
    (('mach',), 3),
    (('temp',), 1),
    (('pressure', 'p44_hpa', 'p45_hpa', 'baro_pressure_setting'), 1),
    (('hum', 'rh'), 0),
]

def _to_datetime(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc)

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
        if not pl.datatypes.is_numeric(dtype):
            continue
        applied = False
        for substrings, step in STEP_QUANTIZATION:
            if any(sub in col for sub in substrings):
                exprs.append(((pl.col(col) / step).round(0) * step).alias(col))
                applied = True
                break
        if applied:
            continue
        for substrings, decimals in DECIMAL_QUANTIZATION:
            if any(sub in col for sub in substrings):
                exprs.append(pl.col(col).round(decimals).alias(col))
                break
    if exprs:
        df = df.with_columns(exprs)
    return df

class BeastDF(TcpClient):
    def __init__(self, host, port, ref_lat=None, ref_lon=None):
        super().__init__(host, port, 'beast')
        self.records = []
        self.position_cache = {}  # {icao: {'even': (msg, ts), 'odd': (msg, ts)}}
        self.msg_counts = defaultdict(int)  # Track message statistics
        self.ref_lat = ref_lat
        self.ref_lon = ref_lon
        
    def handle_messages(self, messages):
        for raw_bytes, ts in messages:
            # Convert to hex string
            if isinstance(raw_bytes, (bytes, bytearray)):
                msg = raw_bytes.hex()
            else:
                msg = raw_bytes.strip()
            
            # Basic validation
            if len(msg) != 28:
                continue
                
            # CRC check
            if pms.crc(msg) != 0:
                self.msg_counts['crc_fail'] += 1
                continue
                
            df = pms.df(msg)
            icao = pms.icao(msg)
            
            if not icao:
                continue
                
            self.msg_counts[f'df{df}'] += 1
            
            # Base record
            rec = {
                'timestamp': ts,
                'datetime_utc': _to_datetime(ts),
                'msg': msg,  # Store raw message
                'msg_hash': hashlib.blake2s(msg.encode('utf-8'), digest_size=8).hexdigest(),
                'df': df,
                'icao': icao,
            }
            
            # Process ADS-B messages (DF 17/18)
            if df in [17, 18]:
                tc = pms.adsb.typecode(msg)
                rec['typecode'] = tc
                self.msg_counts[f'tc{tc}'] += 1
                
                # Decode all available fields
                for fname, func in ADSB_FUNCS.items():
                    try:
                        val = func(msg)
                        if val is not None and val != (None, None):
                            rec[fname] = val
                    except:
                        pass
                
                # Handle position messages specially
                if tc in range(5, 23):  # All position messages
                    self._handle_position_message(msg, ts, icao, tc, rec)
                    
            # Process Comm-B messages (DF 20/21)
            elif df in [20, 21]:
                # Try to infer BDS code
                try:
                    bds_code = pms.bds.infer(msg, mrar=True)
                    rec['bds'] = bds_code
                    
                    if bds_code:
                        self.msg_counts[f'bds{bds_code}'] += 1
                except:
                    rec['bds'] = None
                
                # Check all BDS flags
                for bds_name, module in BDS_FLAGS.items():
                    try:
                        fn_name = f'is{bds_name[3:]}'
                        if hasattr(module, fn_name):
                            fn = getattr(module, fn_name)
                            rec[fn_name] = fn(msg)
                    except:
                        pass
                
                # Decode Comm-B data
                for key, func in COMMB_FUNCS.items():
                    try:
                        val = func(msg)
                        if val is not None:
                            rec[key] = val
                    except:
                        pass
            
            # Process surveillance altitude (DF 4/5)
            elif df in [4, 5]:
                try:
                    rec['altitude'] = pms.common.altcode(msg)
                except:
                    pass
            
            # Process all-call replies (DF 11)
            elif df == 11:
                try:
                    rec['capability'] = pms.common.ca(msg)
                except:
                    pass
                    
            self.records.append(rec)
    
    def _handle_position_message(self, msg, ts, icao, tc, rec):
        """Handle position decoding with even/odd message pairs."""
        if tc not in range(5, 23):
            return
            
        oe_flag = pms.adsb.oe_flag(msg)
        rec['oe_flag'] = oe_flag
        
        # Initialize position cache for this aircraft
        if icao not in self.position_cache:
            self.position_cache[icao] = {}
        
        # Store message based on even/odd flag
        if oe_flag == 0:
            self.position_cache[icao]['even'] = (msg, ts)
        else:
            self.position_cache[icao]['odd'] = (msg, ts)
        
        # Try to decode position if we have both messages
        if 'even' in self.position_cache[icao] and 'odd' in self.position_cache[icao]:
            even_msg, even_ts = self.position_cache[icao]['even']
            odd_msg, odd_ts = self.position_cache[icao]['odd']
            
            # Messages should be within 10 seconds
            if abs(even_ts - odd_ts) < 10:
                try:
                    # Surface position (TC 5-8)
                    if 5 <= tc <= 8:
                        if self.ref_lat and self.ref_lon:
                            lat, lon = pms.adsb.surface_position(
                                even_msg, odd_msg, even_ts, odd_ts, 
                                self.ref_lat, self.ref_lon
                            )
                            rec['latitude'] = lat
                            rec['longitude'] = lon
                            rec['position_type'] = 'surface'
                    # Airborne position
                    else:
                        lat, lon = pms.adsb.airborne_position(
                            even_msg, odd_msg, even_ts, odd_ts
                        )
                        rec['latitude'] = lat
                        rec['longitude'] = lon
                        rec['position_type'] = 'airborne'
                except:
                    # Could also try position_with_ref if available
                    if self.ref_lat and self.ref_lon:
                        try:
                            lat, lon = pms.adsb.position_with_ref(
                                msg, self.ref_lat, self.ref_lon
                            )
                            rec['latitude'] = lat
                            rec['longitude'] = lon
                            rec['position_type'] = 'with_ref'
                        except:
                            pass
                            
    def get_statistics(self):
        """Return message statistics."""
        return dict(self.msg_counts)

if __name__ == "__main__":
    host = '129.123.91.145'
    port = 30005
    
    # The location of receiver (Vernal, USU campus)

    ref_lat = 40.46014413068818
    ref_lon = -109.56578602889579
    
    client = BeastDF(host, port, ref_lat, ref_lon)
    
    # Set up timeout
    signal.signal(signal.SIGALRM, _alarm_handler)
    n_sec = 15
    signal.alarm(n_sec)
    
    try:
        client.run()
    except TimeoutException:
        print(f"\n→ {n_sec} seconds elapsed, stopping capture.")
    finally:
        signal.alarm(0)
    
    # Print statistics
    print("\nMessage Statistics:")
    stats = client.get_statistics()
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    
    # Create DataFrame
    records = [_flatten_record(rec) for rec in client.records]
    data_df = pl.DataFrame(records)
    
    if data_df.height > 0:
        sort_cols = [c for c in ['icao', 'datetime_utc'] if c in data_df.columns]
        if sort_cols:
            data_df = data_df.sort(sort_cols)

        data_df = _apply_quantization(data_df)
        
        core_cols = [
            'timestamp',
            'datetime_utc',
            'icao',
            'df',
            'typecode',
            'msg_hash',
            'latitude',
            'longitude',
            'position_type',
            'altitude',
            'selected_altitude_ft',
            'velocity_gs',
            'velocity_track',
            'velocity_vr',
            'velocity_type',
            'airborne_speed',
            'airborne_heading',
            'airborne_vr',
            'airborne_type',
            'spdhdg_speed',
            'spdhdg_heading',
            'baro_pressure_setting',
            'callsign',
            'category',
        ]
        core_cols = [c for c in core_cols if c in data_df.columns]
        key_cols = [c for c in ['timestamp', 'datetime_utc', 'icao', 'msg_hash'] if c in data_df.columns]

        core_df = data_df.select(core_cols) if core_cols else data_df
        derived_cols = [c for c in data_df.columns if c not in set(core_cols)]
        derived_df = data_df.select(key_cols + derived_cols) if derived_cols else data_df.select(key_cols)

        # Save to Parquet (core + derived)
        core_df.write_parquet('adsb_core.parquet', compression='zstd')
        derived_df.write_parquet('adsb_derived.parquet', compression='zstd')
        
        total_records = data_df.height
        unique_aircraft = data_df.select(pl.col('icao').n_unique()).item() if 'icao' in data_df.columns else 0
        print(f"\nTotal records: {total_records}")
        print(f"Unique aircraft: {unique_aircraft}")
        
        # Show position success rate
        if 'latitude' in data_df.columns:
            pos_success = data_df.select(pl.col('latitude').is_not_null().sum()).item()
            print(f"Successful position decodes: {pos_success}/{total_records} ({pos_success/total_records*100:.1f}%)")

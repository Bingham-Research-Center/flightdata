import signal
import inspect

import pyModeS as pms
from pyModeS.extra.tcpclient import TcpClient
import pandas as pd

class TimeoutException(Exception):
    pass

def _alarm_handler(signum, frame):
    raise TimeoutException()

adfb_funcs = {
    name: func
    for name, func in inspect.getmembers(pms.adsb, inspect.isfunction)
    if name not in ("crc",)    # skip helpers
}

# 1) Build BDS-flag and Comm-B functions:
BDS_FLAGS = {
    name: getattr(pms.bds, name)
    for name in ("bds10","bds17","bds20","bds30","bds40","bds44","bds50","bds60")
}

COMMB_FUNCS = {
    # basic capability & callsign
    "ovc10":   pms.commb.ovc10,
    "cap17":   pms.commb.cap17,
    "cs20":    pms.commb.cs20,
    # selected-altitude
    "selalt40_mcp": pms.commb.selalt40mcp,
    "selalt40_fms": pms.commb.selalt40fms,
    "p40_baro":     pms.commb.p40baro,
    # roll/track/GS/TAS
    "roll50": pms.commb.roll50,
    "trk50":  pms.commb.trk50,
    "gs50":   pms.commb.gs50,
    "rtrk50": pms.commb.rtrk50,
    "tas50":  pms.commb.tas50,
    # heading/IAS/Mach/VR
    "hdg60":     pms.commb.hdg60,
    "ias60":     pms.commb.ias60,
    "mach60":    pms.commb.mach60,
    "vr60_baro": pms.commb.vr60baro,
    "vr60_ins":  pms.commb.vr60ins,
    # experimental weather (requires mrar=True)
    "wind44": pms.commb.wind44,
    "temp44": pms.commb.temp44,
    "p44":     pms.commb.p44,
    "hum44":   pms.commb.hum44,
    "turb45":  pms.commb.turb45,
    "ws45":    pms.commb.ws45,
    "mb45":    pms.commb.mb45,
    "ic45":    pms.commb.ic45,
    "wv45":    pms.commb.wv45,
    "temp45":  pms.commb.temp45,
    "p45":     pms.commb.p45,
    "rh45":    pms.commb.rh45,
}

class BeastDF(TcpClient):
    def __init__(self, host, port):
        super().__init__(host, port, 'beast')
        self.records = []

        # Track even/odd messages for position decoding
        self.position_cache = {}  # {"icao": {'even': (msg, ts), 'odd': (msg, ts)}}

    def handle_messages(self, messages):
        for raw_bytes, ts in messages:
            # hex-string guard
            if isinstance(raw_bytes, (bytes, bytearray)):
                msg = raw_bytes.hex()
            else:
                msg = raw_bytes.strip()

            # sanity check
            if len(msg) != 28 or pms.crc(msg) != 0:
                continue

            df = pms.df(msg)

            # pms.bds.infer(msg, mrar=True)

            rec = {
                'datetime_utc': pd.to_datetime(ts, unit='s', utc=True),
                'timestamp': ts,
                'df': df,
                'icao': pms.icao(msg),
            }



            # Process ADS-B messages (DF 17/18)
            if df in [17, 18]:
                tc = pms.adsb.typecode(msg)
                rec['typecode'] = tc

                # Decode based on typecode
                for fname, func in adfb_funcs.items():
                    try:
                        val = func(msg)
                        if val is not None and val != (None, None):
                            rec[fname] = val
                    except:
                        continue

                if tc in range(9, 19):  # Position messages
                    oe_flag = pms.adsb.oe_flag(msg)

                    icao = pms.icao(msg)
                    if icao not in self.position_cache:
                        self.position_cache[icao] = {}

                    if oe_flag == 0:
                        self.position_cache[icao]['even'] = (msg, ts)
                    else:
                        self.position_cache[icao]['odd'] = (msg, ts)

                    # Try to decode position if we have both
                    if 'even' in self.position_cache[icao] and 'odd' in self.position_cache[icao]:
                        even_msg, even_ts = self.position_cache[icao]['even']
                        odd_msg, odd_ts = self.position_cache[icao]['odd']

                        # Only decode if messages are recent (within 10 seconds)
                        if abs(even_ts - odd_ts) < 10:
                            try:
                                lat, lon = pms.adsb.position(even_msg, odd_msg, even_ts, odd_ts)
                                rec['latitude'] = lat
                                rec['longitude'] = lon
                            except:
                                pass

            # Process Comm-B messages (DF 20/21)
            elif df in [20, 21]:
                # Infer BDS code with MRAR support
                bds_code = pms.bds.infer(msg, mrar=True)
                rec['bds'] = bds_code

                # Check all BDS flags
                for bds_name, module in BDS_FLAGS.items():
                    fn = getattr(module, f"is{bds_name[3:]}")
                    rec[f"is{bds_name[3:]}"] = fn(msg)

                # Decode Comm-B functions
                for key, func in COMMB_FUNCS.items():
                    try:
                        rec[key] = func(msg)
                    except:
                        rec[key] = None

            self.records.append(rec)

if __name__ == "__main__":
    host = '129.123.91.145'
    port = 30005
    client = BeastDF(host, port)

    # hook up the alarm
    signal.signal(signal.SIGALRM, _alarm_handler)
    n_sec = 15
    signal.alarm(n_sec)

    try:
        client.run()
    except TimeoutException:
        print(f"\n→ {n_sec} seconds elapsed, stopping capture.")
    finally:
        signal.alarm(0)    # cancel any pending alarm

    data_df = pd.DataFrame(client.records)
    data_df['datetime_utc'] = pd.to_datetime(data_df['timestamp'], unit='s', utc=True)
    data_df = data_df.set_index(['icao', 'datetime_utc']).sort_index()

    # Save this to disc as a CSV file
    data_df.to_csv('adsb_data2.csv', index=True)

    # print(df)


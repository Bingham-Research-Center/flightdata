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

            pms.bds.infer(msg, mrar=True)

            # 3) seed your record
            rec = {
                'timestamp': ts,
                'df':        pms.df(msg),
                'icao':      pms.adsb.icao(msg),
            }

            # 4) run through each BDS-flag module
            for bds_name, module in BDS_FLAGS.items():
                # each module has an isXX() method
                fn = getattr(module, f"is{bds_name[3:]}")
                rec[f"is{bds_name[3:]}"] = fn(msg)

            # 5) run through each Comm-B weather/capability function
            for key, _func in COMMB_FUNCS.items():
                try:
                    rec[key] = _func(msg)
                except Exception:
                    rec[key] = None

            for fname, func in adfb_funcs.items():
                try:
                    val = func(msg)
                    if val is not None and val != (None, None):
                        rec[fname] = val
                except Exception:
                    continue

            # 6) append for DataFrame later
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

    df = pd.DataFrame(client.records)

    round_time_column = False
    if round_time_column == True:
        df['datetime_utc'] = (
            pd.to_datetime(df['timestamp'], unit='s', utc=True))

    # Leaving index as unique identifier
    # df = df.set_index('datetime_utc')

    # Group by aircraft identifier (ICAO, column 'icao'), secondly by timestamp
    df = df.groupby('icao').apply(
        lambda x: x.set_index('datetime_utc').sort_index()
    ).reset_index(level=0, drop=True)

    # Save this to disc as a CSV file
    df.to_csv('adsb_data2.csv', index=True)

    # print(df)


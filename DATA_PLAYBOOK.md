# Data Playbook (Parquet-Only)

This repo now uses Parquet only for captured and shared data products.

## Files in use
- `adsb_core.parquet`: primary capture output (core fields).
- `adsb_derived.parquet`: primary capture output (derived/extended fields).
- `example_2026-03-02_60s_core.parquet`: in-repo sample capture for collaborators.
- `example_2026-03-02_60s_derived.parquet`: matching in-repo sample derived file.

The join key between core and derived files is:
- `timestamp`
- `datetime_utc`
- `icao`
- `msg_hash`

## Quick start
From repo root:

```bash
python adsbdecoder.py --seconds 60
python tools/summary.py adsb_core.parquet adsb_derived.parquet
```

To inspect the in-repo sample:

```bash
python tools/summary.py example_2026-03-02_60s_core.parquet example_2026-03-02_60s_derived.parquet
```

To launch the collaborator notebook:

```bash
jupyter lab
```

Open:
- `notebooks/uinta_basin_proof_of_concept.ipynb`

The notebook loads local capture parquet first, then falls back to the in-repo sample parquet pair.

## Create a shareable snapshot
Create compact collaborator files from a capture:

```bash
python tools/make_collab_snapshot.py \
  --core-in adsb_core.parquet \
  --derived-in adsb_derived.parquet \
  --prefix example_YYYY-MM-DD_60s
```

By default this keeps data compact by dropping raw `msg` from the derived snapshot output.

## Read in Python
Pandas:

```python
import pandas as pd

core = pd.read_parquet("example_2026-03-02_60s_core.parquet")
derived = pd.read_parquet("example_2026-03-02_60s_derived.parquet")

join_cols = ["timestamp", "datetime_utc", "icao", "msg_hash"]
df = core.merge(derived, on=join_cols, how="left")
```

Polars:

```python
import polars as pl

core = pl.read_parquet("example_2026-03-02_60s_core.parquet")
derived = pl.read_parquet("example_2026-03-02_60s_derived.parquet")
df = core.join(derived, on=["timestamp", "datetime_utc", "icao", "msg_hash"], how="left")
```

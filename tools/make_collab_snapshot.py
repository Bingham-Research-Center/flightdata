import argparse
from pathlib import Path

import polars as pl


def _human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def _load_parquet(path: Path, label: str) -> pl.DataFrame:
    if not path.exists():
        raise SystemExit(f"{label} file not found: {path}")
    return pl.read_parquet(path)


def _write_parquet(df: pl.DataFrame, path: Path) -> None:
    df.write_parquet(path, compression="zstd")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create compact collaborator snapshot files from capture parquet outputs."
    )
    parser.add_argument(
        "--core-in",
        default="adsb_core.parquet",
        help="Input core parquet path (default: adsb_core.parquet).",
    )
    parser.add_argument(
        "--derived-in",
        default="adsb_derived.parquet",
        help="Input derived parquet path (default: adsb_derived.parquet).",
    )
    parser.add_argument(
        "--prefix",
        required=True,
        help="Output prefix used for <prefix>_core.parquet and <prefix>_derived.parquet.",
    )
    parser.add_argument(
        "--out-dir",
        default=".",
        help="Output directory for snapshot files (default: current directory).",
    )
    parser.add_argument(
        "--keep-derived-msg",
        action="store_true",
        help="Keep raw 'msg' column in derived output (default drops it for compactness).",
    )
    args = parser.parse_args()

    core_path = Path(args.core_in)
    derived_path = Path(args.derived_in)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    core_df = _load_parquet(core_path, "Core")
    derived_df = _load_parquet(derived_path, "Derived")

    if not args.keep_derived_msg and "msg" in derived_df.columns:
        derived_df = derived_df.drop("msg")

    core_out = out_dir / f"{args.prefix}_core.parquet"
    derived_out = out_dir / f"{args.prefix}_derived.parquet"
    _write_parquet(core_df, core_out)
    _write_parquet(derived_df, derived_out)

    core_size = core_out.stat().st_size
    derived_size = derived_out.stat().st_size
    print(f"Wrote {core_out} ({_human_size(core_size)})")
    print(f"Wrote {derived_out} ({_human_size(derived_size)})")
    print(f"Core shape: {core_df.height} rows x {core_df.width} cols")
    print(f"Derived shape: {derived_df.height} rows x {derived_df.width} cols")


if __name__ == "__main__":
    main()

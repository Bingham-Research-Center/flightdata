import argparse
from pathlib import Path

import polars as pl


def summarize_file(path: Path) -> None:
    if not path.exists():
        print(f"{path}: not found")
        return

    scan = pl.scan_parquet(path)
    cols = scan.columns

    row_count = scan.select(pl.len().alias("rows")).collect().item()
    col_count = len(cols)
    print(f"\n{path.name}")
    print(f"rows: {row_count} | cols: {col_count}")

    if row_count == 0 or col_count == 0:
        return

    nn_exprs = [pl.col(c).is_not_null().sum().alias(c) for c in cols]
    nn = scan.select(nn_exprs).collect().row(0, named=True)

    non_empty = sorted(
        [(c, nn[c]) for c in cols if nn[c] > 0],
        key=lambda x: x[1],
        reverse=True,
    )

    if not non_empty:
        print("non-empty columns: none")
        return

    print("non-empty columns (count):")
    for name, count in non_empty:
        print(f"  {name}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize ADS-B Parquet outputs.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Parquet files to summarize (default: adsb_core.parquet adsb_derived.parquet).",
    )
    args = parser.parse_args()

    if args.paths:
        for p in args.paths:
            summarize_file(Path(p))
        return

    for default_name in ("adsb_core.parquet", "adsb_derived.parquet"):
        summarize_file(Path(default_name))


if __name__ == "__main__":
    main()

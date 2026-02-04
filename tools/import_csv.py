import argparse
from pathlib import Path

import polars as pl


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert legacy CSV to Parquet.")
    parser.add_argument("csv_path", help="Path to CSV file (e.g., example_output.csv).")
    parser.add_argument(
        "--out",
        help="Output Parquet path (default: <csv_stem>.parquet).",
        default=None,
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        raise SystemExit(f"CSV not found: {csv_path}")

    out_path = Path(args.out) if args.out else csv_path.with_suffix(".parquet")
    df = pl.read_csv(csv_path, infer_schema_length=1000)
    df.write_parquet(out_path, compression="zstd")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

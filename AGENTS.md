# Repository Guidelines

## Project Structure & Module Organization
- `adsbdecoder.py` is the primary ADS-B decoding script and entry point.
- `example_output.csv` is a sample output file; the script currently writes `adsb_core.parquet` and `adsb_derived.parquet` in the repo root.
- `DERIVED_FEATURES.md` documents the scientific feature roadmap and hypotheses.
- `units.md` is the column → unit mapping table.

## Build, Test, and Development Commands
- `python adsbdecoder.py` runs a 15-second capture and decodes messages from the configured receiver, then writes a Parquet file.
- `pip install pyModeS polars` installs the Python dependencies needed to run the script.
- There is no build step; run directly from the repo root.

## Coding Style & Naming Conventions
- Python, 4-space indentation, and `snake_case` for functions/variables.
- Module-level constants use `ALL_CAPS` (e.g., `ADSB_FUNCS`, `BDS_FLAGS`).
- Keep decoding logic tolerant of malformed messages and avoid breaking the stream on single-message failures.

## Testing Guidelines
- No automated test suite exists yet.
- Manual validation: run `python adsbdecoder.py` and confirm a non-empty Parquet file plus reasonable summary stats in stdout.
- If you change output fields, update `example_output.csv` or note the change in your PR.
- Keep `units.md` in sync with any schema or derived‑feature changes.

## Commit & Pull Request Guidelines
- Commit history uses short, sentence-case summaries without prefixes; follow the same style.
- PRs should include: summary of changes, how to run (commands), and sample output if decoding behavior changes.

## Configuration & Data Notes
- Receiver configuration lives in the `__main__` block of `adsbdecoder.py` (`host`, `port`, `ref_lat`, `ref_lon`).
- Keep site-specific coordinates out of shared commits unless required; document defaults in the PR description.

import argparse
from pathlib import Path

import pypandoc


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render markdown to a scientific-style PDF using pandoc + xelatex."
    )
    parser.add_argument("source", help="Path to source markdown file.")
    parser.add_argument(
        "--out",
        default=None,
        help="Output PDF path (default: <source_stem>.pdf next to source).",
    )
    parser.add_argument(
        "--header",
        default="tools/pdf_scientific_header.tex",
        help="Path to LaTeX header include for styling.",
    )
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        raise SystemExit(f"Source markdown not found: {source}")

    header = Path(args.header)
    if not header.exists():
        raise SystemExit(f"Header file not found: {header}")

    out_path = Path(args.out) if args.out else source.with_suffix(".pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    extra_args = [
        "--standalone",
        "--from=gfm",
        "--pdf-engine=xelatex",
        f"--include-in-header={header.resolve()}",
        "-V",
        "fontsize=11pt",
    ]

    pypandoc.convert_file(
        str(source.resolve()),
        to="pdf",
        outputfile=str(out_path.resolve()),
        extra_args=extra_args,
    )

    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

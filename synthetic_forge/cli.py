"""Command-line entry point.

    python -m synthetic_forge --companies 8 --seed 42 --out ./out --format csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .generator import DatasetSpec, generate
from .validate import validate_integrity


def _write_json(data, out_dir: Path) -> None:
    for table, rows in data.items():
        (out_dir / f"{table}.json").write_text(
            json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def _write_csv(data, out_dir: Path) -> None:
    for table, rows in data.items():
        path = out_dir / f"{table}.csv"
        if not rows:
            path.write_text("", encoding="utf-8")
            continue
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="synthetic_forge", description=__doc__)
    parser.add_argument("--companies", type=int, default=8)
    parser.add_argument("--months", type=int, default=18, help="months of invoice history")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("./out"))
    parser.add_argument("--format", choices=("csv", "json"), default="csv")
    parser.add_argument("--validate-only", action="store_true",
                        help="generate in memory, print the integrity report, write nothing")
    args = parser.parse_args(argv)

    spec = DatasetSpec(companies=args.companies, months_of_history=args.months, seed=args.seed)
    data = generate(spec)

    report = validate_integrity(data)
    print(report, file=sys.stderr)
    if not report.ok:
        return 1
    if args.validate_only:
        return 0

    args.out.mkdir(parents=True, exist_ok=True)
    (_write_csv if args.format == "csv" else _write_json)(data, args.out)
    print(f"\nWrote {len(data)} tables to {args.out.resolve()} ({args.format})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

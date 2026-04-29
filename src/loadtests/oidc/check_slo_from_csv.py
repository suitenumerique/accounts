"""Validate OIDC load test SLO from Locust CSV output."""

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SLOThresholds:
    """Thresholds used to validate performance and reliability."""

    max_failure_pct: float
    max_p95_ms: float
    max_p99_ms: float


@dataclass(frozen=True)
class RowResult:
    """Computed metrics extracted from one Locust CSV row."""

    request_type: str
    name: str
    request_count: int
    failure_count: int
    failure_pct: float
    p95_ms: float
    p99_ms: float


def _as_float(value: str) -> float:
    cleaned = (value or "").strip().replace(",", ".")
    if cleaned == "":
        return 0.0
    return float(cleaned)


def _as_int(value: str) -> int:
    return int(_as_float(value))


def _load_stats(csv_prefix: str) -> list[dict[str, str]]:
    stats_path = Path(f"{csv_prefix}_stats.csv")
    if not stats_path.exists():
        raise FileNotFoundError(f"Locust stats file not found: {stats_path}")

    with stats_path.open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def _compute_result(row: dict[str, str]) -> RowResult:
    request_count = _as_int(row.get("Request Count", "0"))
    failure_count = _as_int(row.get("Failure Count", "0"))
    failure_pct = 0.0 if request_count == 0 else (failure_count / request_count) * 100

    return RowResult(
        request_type=row.get("Type", ""),
        name=row.get("Name", ""),
        request_count=request_count,
        failure_count=failure_count,
        failure_pct=failure_pct,
        p95_ms=_as_float(row.get("95%", "0")),
        p99_ms=_as_float(row.get("99%", "0")),
    )


def _select_rows(rows: list[dict[str, str]], include_flow_rows: bool) -> list[RowResult]:
    selected = []
    for row in rows:
        name = row.get("Name", "")
        request_type = row.get("Type", "")

        if name == "Aggregated":
            selected.append(_compute_result(row))
            continue

        if include_flow_rows and request_type == "FLOW" and name.startswith("full-e2e:"):
            selected.append(_compute_result(row))

    return selected


def _validate(results: list[RowResult], thresholds: SLOThresholds) -> list[str]:
    failures: list[str] = []
    for result in results:
        label = f"{result.request_type}/{result.name}"
        if result.failure_pct > thresholds.max_failure_pct:
            failure_message = (
                f"{label}: failure_pct {result.failure_pct:.2f}% "
                f"> {thresholds.max_failure_pct:.2f}%"
            )
            failures.append(
                failure_message
            )
        if result.p95_ms > thresholds.max_p95_ms:
            failures.append(
                f"{label}: p95 {result.p95_ms:.2f}ms > {thresholds.max_p95_ms:.2f}ms"
            )
        if result.p99_ms > thresholds.max_p99_ms:
            failures.append(
                f"{label}: p99 {result.p99_ms:.2f}ms > {thresholds.max_p99_ms:.2f}ms"
            )

    return failures


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--csv-prefix",
        required=True,
        help="Prefix used by Locust --csv (expects <prefix>_stats.csv).",
    )
    parser.add_argument("--max-failure-pct", type=float, default=1.0)
    parser.add_argument("--max-p95-ms", type=float, default=1500.0)
    parser.add_argument("--max-p99-ms", type=float, default=2500.0)
    parser.add_argument(
        "--include-flow-rows",
        action="store_true",
        help="Also validate FLOW/full-e2e:* rows, not only Aggregated.",
    )
    return parser.parse_args()


def main() -> int:
    """Program entrypoint."""
    args = parse_args()
    rows = _load_stats(args.csv_prefix)
    selected = _select_rows(rows, include_flow_rows=args.include_flow_rows)

    if not selected:
        print("No matching rows found in Locust stats CSV.")  # noqa: T201
        return 2

    thresholds = SLOThresholds(
        max_failure_pct=args.max_failure_pct,
        max_p95_ms=args.max_p95_ms,
        max_p99_ms=args.max_p99_ms,
    )
    failures = _validate(selected, thresholds)

    for result in selected:
        print(  # noqa: T201
            " - ".join(
                [
                    f"{result.request_type}/{result.name}",
                    f"count={result.request_count}",
                    f"fail={result.failure_pct:.2f}%",
                    f"p95={result.p95_ms:.2f}ms",
                    f"p99={result.p99_ms:.2f}ms",
                ]
            )
        )

    if failures:
        print("SLO check: FAILED")  # noqa: T201
        for failure in failures:
            print(f"  * {failure}")  # noqa: T201
        return 1

    print("SLO check: OK")  # noqa: T201
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

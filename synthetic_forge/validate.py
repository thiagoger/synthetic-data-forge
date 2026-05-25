"""Referential-integrity validator.

A synthetic dataset is only useful if its foreign keys actually resolve.
This module re-checks the whole graph after generation and reports any
dangling reference -- the same gate you would run before loading data into
a real database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# child_table.column -> parent_table.id
_FOREIGN_KEYS = {
    ("users", "company_id"): "companies",
    ("subscriptions", "company_id"): "companies",
    ("subscriptions", "owner_user_id"): "users",
    ("invoices", "company_id"): "companies",
    ("invoices", "subscription_id"): "subscriptions",
    ("invoice_line_items", "invoice_id"): "invoices",
}


@dataclass
class IntegrityReport:
    row_counts: dict[str, int] = field(default_factory=dict)
    violations: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def __str__(self) -> str:
        lines = ["Row counts:"]
        for table, n in self.row_counts.items():
            lines.append(f"  {table:<22} {n:>8,}")
        if self.ok:
            lines.append("\nReferential integrity: PASS (0 dangling references)")
        else:
            lines.append(f"\nReferential integrity: FAIL ({len(self.violations)} violations)")
            lines.extend(f"  - {v}" for v in self.violations[:20])
        return "\n".join(lines)


def validate_integrity(data: dict[str, list[dict[str, Any]]]) -> IntegrityReport:
    report = IntegrityReport(row_counts={t: len(rows) for t, rows in data.items()})

    # Build id sets for every parent table once.
    id_sets = {table: {row["id"] for row in rows} for table, rows in data.items()}

    for (child_table, column), parent_table in _FOREIGN_KEYS.items():
        parent_ids = id_sets.get(parent_table, set())
        for row in data.get(child_table, []):
            value = row.get(column)
            if value is None:
                continue
            if value not in parent_ids:
                report.violations.append(
                    f"{child_table}.{column}={value} has no matching {parent_table}.id"
                )

    return report

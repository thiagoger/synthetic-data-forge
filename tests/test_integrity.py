"""Tests: determinism and referential integrity."""

from synthetic_forge import DatasetSpec, generate, validate_integrity


def test_referential_integrity_holds():
    data = generate(DatasetSpec(companies=10, seed=7))
    report = validate_integrity(data)
    assert report.ok, report.violations


def test_generation_is_deterministic():
    a = generate(DatasetSpec(companies=5, seed=123))
    b = generate(DatasetSpec(companies=5, seed=123))
    assert a == b


def test_different_seeds_differ():
    a = generate(DatasetSpec(companies=5, seed=1))
    b = generate(DatasetSpec(companies=5, seed=2))
    assert a != b


def test_invoice_total_matches_line_items():
    data = generate(DatasetSpec(companies=6, seed=99))
    line_sum: dict[int, float] = {}
    for li in data["invoice_line_items"]:
        line_sum[li["invoice_id"]] = round(line_sum.get(li["invoice_id"], 0.0) + li["amount"], 2)
    for inv in data["invoices"]:
        assert abs(inv["total"] - line_sum[inv["id"]]) < 0.01


def test_every_invoice_has_line_items():
    data = generate(DatasetSpec(companies=4, seed=3))
    invoice_ids = {inv["id"] for inv in data["invoices"]}
    referenced = {li["invoice_id"] for li in data["invoice_line_items"]}
    assert invoice_ids == referenced

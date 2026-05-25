# synthetic-data-forge

> Deterministic, referentially-intact synthetic datasets for demos, tests, and ML — zero runtime dependencies.

Realistic demo environments fall apart when the data doesn't hang together: invoices point at customers that don't exist, totals don't match line items, and re-running the generator produces a different database every time. **synthetic-data-forge** generates a connected graph of business records where every foreign key resolves to a real parent row, the totals reconcile, and the same seed always produces byte-identical output.

Built as a distilled, open version of the synthetic-data approach I use in production to stand up multi-entity demo environments (companies → users → subscriptions → invoices → line items).

## Why it exists

- **Referential integrity by construction** — children are only ever attached to parents that already exist, then re-validated end to end.
- **Deterministic** — output is a pure function of the seed, so demos and test fixtures are reproducible across machines and CI.
- **Reconciled** — every invoice total equals the sum of its line items.
- **Zero dependencies** — standard library only; runs anywhere Python 3.10+ runs.

## Quick start

```bash
# Generate 8 companies with 18 months of invoice history, as CSV
python -m synthetic_forge --companies 8 --months 18 --seed 42 --out ./out --format csv

# Just check integrity, write nothing
python -m synthetic_forge --validate-only
```

Output (to stderr):

```
Row counts:
  companies                     8
  users                       112
  subscriptions                 8
  invoices                    144
  invoice_line_items          287

Referential integrity: PASS (0 dangling references)
```

## As a library

```python
from synthetic_forge import DatasetSpec, generate, validate_integrity

data = generate(DatasetSpec(companies=50, months_of_history=24, seed=7))
report = validate_integrity(data)
assert report.ok

invoices = data["invoices"]          # list[dict], every company_id resolves
print(report)                        # row counts + integrity verdict
```

## Schema

```
companies ─┬─< users
           ├─< subscriptions ─< invoices ─< invoice_line_items
           └─< invoices
```

| Table | Key columns | Foreign keys |
|-------|-------------|--------------|
| `companies` | `id` | — |
| `users` | `id` | `company_id` → companies |
| `subscriptions` | `id` | `company_id` → companies, `owner_user_id` → users |
| `invoices` | `id` | `company_id` → companies, `subscription_id` → subscriptions |
| `invoice_line_items` | `id` | `invoice_id` → invoices |

## Tests

```bash
pip install pytest
pytest -q
```

Covers determinism, foreign-key integrity, invoice/line-item reconciliation, and orphan detection.

## License

MIT — see [LICENSE](LICENSE).

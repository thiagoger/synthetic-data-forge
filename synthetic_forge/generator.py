"""Core generator.

Builds a connected graph of business records where every foreign key
resolves to a real parent row. The whole dataset is a pure function of the
random seed, so the same seed always produces byte-identical output -- which
is what makes synthetic data usable for reproducible demos and tests.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

# Small built-in pools keep this dependency-free. Swap for Faker if you want
# more variety; the generator only needs callables that return strings.
_INDUSTRIES = (
    "Construction", "Healthcare", "Manufacturing", "Professional Services",
    "Retail", "Logistics", "Non-Profit", "Technology", "Hospitality",
)
_FIRST = (
    "Ana", "Bruno", "Carla", "Diego", "Elena", "Felipe", "Grace", "Hugo",
    "Iris", "Joao", "Karen", "Lucas", "Maya", "Noah", "Olivia", "Pedro",
)
_LAST = (
    "Silva", "Costa", "Nguyen", "Patel", "Garcia", "Rossi", "Khan", "Mueller",
    "Santos", "Oliveira", "Tanaka", "Abbas", "Lopez", "Novak", "Reis",
)
_PLANS = (
    ("Starter", 49.0), ("Growth", 199.0), ("Scale", 599.0), ("Enterprise", 1999.0),
)
_LINE_ITEMS = (
    ("Base subscription", 1), ("Additional seats", 5), ("Premium support", 1),
    ("API overage", 3), ("Onboarding", 1), ("Data migration", 1),
)


@dataclass
class DatasetSpec:
    """Knobs for dataset size and shape."""

    companies: int = 8
    users_per_company: tuple[int, int] = (3, 25)
    months_of_history: int = 18
    invoice_paid_rate: float = 0.82  # fraction of invoices marked paid
    seed: int = 42
    start_date: date = field(default_factory=lambda: date(2024, 1, 1))


def _money(value: float) -> float:
    return round(value, 2)


def generate(spec: DatasetSpec) -> dict[str, list[dict[str, Any]]]:
    """Return a dict of table_name -> list of row dicts.

    Tables: companies, users, subscriptions, invoices, invoice_line_items.
    Every child row references an existing parent by id.
    """

    rng = random.Random(spec.seed)
    companies: list[dict[str, Any]] = []
    users: list[dict[str, Any]] = []
    subscriptions: list[dict[str, Any]] = []
    invoices: list[dict[str, Any]] = []
    line_items: list[dict[str, Any]] = []

    next_user_id = 1
    next_sub_id = 1
    next_invoice_id = 1
    next_line_id = 1

    for company_id in range(1, spec.companies + 1):
        industry = rng.choice(_INDUSTRIES)
        companies.append({
            "id": company_id,
            "name": f"{rng.choice(_LAST)} {industry.split()[0]} Co.",
            "industry": industry,
            "created_at": (spec.start_date - timedelta(days=rng.randint(0, 400))).isoformat(),
            "country": rng.choice(("US", "BR", "CA", "UK", "DE")),
        })

        # Users for this company.
        lo, hi = spec.users_per_company
        company_user_ids: list[int] = []
        for _ in range(rng.randint(lo, hi)):
            users.append({
                "id": next_user_id,
                "company_id": company_id,  # FK -> companies.id
                "name": f"{rng.choice(_FIRST)} {rng.choice(_LAST)}",
                "role": rng.choice(("admin", "member", "viewer")),
                "is_active": rng.random() > 0.1,
            })
            company_user_ids.append(next_user_id)
            next_user_id += 1

        # One active subscription per company, owned by an admin user.
        plan_name, plan_price = rng.choice(_PLANS)
        owner_id = rng.choice(company_user_ids)
        subscriptions.append({
            "id": next_sub_id,
            "company_id": company_id,        # FK -> companies.id
            "owner_user_id": owner_id,       # FK -> users.id
            "plan": plan_name,
            "monthly_price": plan_price,
            "status": "active",
        })

        # Monthly invoices across the history window.
        for month in range(spec.months_of_history):
            issued = spec.start_date + timedelta(days=30 * month)
            paid = rng.random() < spec.invoice_paid_rate
            invoice_id = next_invoice_id
            invoice_total = 0.0

            # Each invoice gets 1-3 line items that sum to the invoice total.
            for _ in range(rng.randint(1, 3)):
                desc, max_qty = rng.choice(_LINE_ITEMS)
                qty = rng.randint(1, max_qty)
                unit = _money(plan_price * rng.uniform(0.2, 1.0))
                amount = _money(unit * qty)
                invoice_total += amount
                line_items.append({
                    "id": next_line_id,
                    "invoice_id": invoice_id,  # FK -> invoices.id
                    "description": desc,
                    "quantity": qty,
                    "unit_price": unit,
                    "amount": amount,
                })
                next_line_id += 1

            invoices.append({
                "id": invoice_id,
                "company_id": company_id,        # FK -> companies.id
                "subscription_id": next_sub_id,  # FK -> subscriptions.id
                "issued_date": issued.isoformat(),
                "due_date": (issued + timedelta(days=30)).isoformat(),
                "total": _money(invoice_total),
                "status": "paid" if paid else "open",
                "paid_date": (issued + timedelta(days=rng.randint(1, 29))).isoformat() if paid else None,
            })
            next_invoice_id += 1

        next_sub_id += 1

    return {
        "companies": companies,
        "users": users,
        "subscriptions": subscriptions,
        "invoices": invoices,
        "invoice_line_items": line_items,
    }

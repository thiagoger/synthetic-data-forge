"""synthetic-data-forge — deterministic, referentially-intact synthetic datasets.

Generate realistic multi-table business data (companies -> users ->
subscriptions -> invoices -> line items) with guaranteed foreign-key
integrity, deterministic seeding, and a built-in validator.

Zero runtime dependencies: standard library only.
"""

from .generator import DatasetSpec, generate
from .validate import validate_integrity, IntegrityReport

__all__ = ["DatasetSpec", "generate", "validate_integrity", "IntegrityReport"]
__version__ = "0.1.0"

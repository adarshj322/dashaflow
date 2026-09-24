"""Error taxonomy for DashaFlow.

All input-validation errors subclass both :class:`DashaFlowError` and
:class:`ValueError`, so existing ``pytest.raises(ValueError)`` call sites
and downstream ``except ValueError`` handlers keep working.
"""

from __future__ import annotations


class DashaFlowError(Exception):
    """Base class for all DashaFlow errors."""


class InvalidInputError(DashaFlowError, ValueError):
    """Raised when caller-supplied data (dates, coordinates, paths) is invalid."""


class EphemerisError(DashaFlowError):
    """Raised when the Swiss Ephemeris backend cannot fulfil a computation
    (missing data files, out-of-range failure, house-system failure)."""


class CalculationError(DashaFlowError):
    """Raised when an internal computation produces an implausible result,
    e.g. a chart that violates the output contract."""

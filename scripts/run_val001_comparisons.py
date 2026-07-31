#!/usr/bin/env python3
"""Refuse the superseded PR38 analyzer entry point.

The original bytes remain available in commit 6e51d914 and its result remains
retained for audit. Corrected execution requires the separately committed
freeze, authority, activation, and single-invocation ledger.
"""
raise SystemExit(
    "SUPERSEDED_FOR_GOVERNANCE: use run_val001_corrected_comparison.py only "
    "under the corrected pre-execution authority and activation records"
)

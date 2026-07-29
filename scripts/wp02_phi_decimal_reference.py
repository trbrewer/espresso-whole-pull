#!/usr/bin/env python3
"""Independent Decimal authority for WP02 phi-factor tests."""
from decimal import Decimal, localcontext


def decimal_phi_factor(text: str, precision: int = 100) -> Decimal:
    with localcontext() as context:
        context.prec = precision
        phi = Decimal(text)
        if phi == 0:
            return Decimal(0)
        if phi < 0 or phi >= 1:
            raise ValueError("phi outside [0,1)")
        one = Decimal(1)
        return (
            phi * (phi * (Decimal(11) * phi - Decimal(15)) + Decimal(6))
            + Decimal(6) * (one - phi) ** 3 * (one - phi).ln()
        ) / (Decimal(6) * (one - phi) ** 2)

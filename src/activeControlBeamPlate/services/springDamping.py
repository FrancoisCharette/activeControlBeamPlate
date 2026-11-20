"""Damping on support springs as a loss factor, shared by the beam's ends and the plate's edges.

A spring's stiffness is complex; its damping is a loss factor η, so that the
imaginary part is η times the real part - the convention of the thesis's
complex moduli (Table 2.2's beam: 35.5e7 / 71e9 is η = 0.5 %). A support is
"damped at η" while every one of its springs that has a stiffness carries
exactly that ratio.
"""

from __future__ import annotations

from collections.abc import Sequence

# Loss factors offered, as fractions: 0 % to 10 %.
lossFactors = (0.0, 0.001, 0.002, 0.004, 0.008, 0.01, 0.02, 0.05, 0.1)
# Relative difference within which two loss factors are the same one.
lossTolerance = 1e-6
# Relative difference within which a real part is still the value a preset put
# there: far below anything typed, well above the rounding of a saved setting.
stiffnessTolerance = 1e-9


def lossFactorText(lossFactor: float) -> str:
    """'0.1 %', '2 %': as a menu or a button says it."""
    return f"{lossFactor * 100:g} %"


def sharedLossFactor(springs: Sequence[complex]) -> float | None:
    """The loss factor the springs share; 0 with no stiffness at all; None if they differ.

    A spring with no stiffness has no loss factor, so it is left out - unless
    it has damping anyway, which no loss factor describes.
    """
    factors = []
    for stiffness in springs:
        if stiffness.real > 0:
            factors.append(stiffness.imag / stiffness.real)
        elif stiffness.imag != 0:
            return None
    if not factors:
        return 0.0
    first = factors[0]
    if all(abs(factor - first) <= lossTolerance * max(1.0, abs(first)) for factor in factors):
        return first
    return None


def offeredLevel(lossFactor: float | None) -> float | None:
    """The offered level `lossFactor` is, if it is one of them."""
    if lossFactor is None:
        return None
    return next((level for level in lossFactors if abs(lossFactor - level) < 1e-9), None)


def damped(stiffness: complex, lossFactor: float) -> complex:
    """The spring with its imaginary part set to `lossFactor` times its real part."""
    return complex(stiffness.real, lossFactor * stiffness.real)


def matches(reals: Sequence[float], expected: Sequence[float]) -> bool:
    """Whether the real parts are exactly the expected ones (within stiffnessTolerance)."""
    return all(
        abs(real - target) <= stiffnessTolerance * abs(target)
        for real, target in zip(reals, expected, strict=True)
    )

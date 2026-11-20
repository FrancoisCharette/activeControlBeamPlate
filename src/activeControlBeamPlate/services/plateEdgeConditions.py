"""Typical edge springs for a boundary condition of the plate, and their damping.

Chapter 5's plate is in pure bending, so each edge has two distributed line
springs (Figure 5.1): transverse, against the edge moving out of the plane,
and rotational, against it turning. An edge is Free (neither held), Simply
Supported (held transversely, free to rotate - Table 5.1's plate) or Clamped
(both held). The thesis gives no stiffness values, so these are this app's
recommendation.

A held spring is `holdingFactor` times the plate's own stiffness across that
edge, per metre of edge: D/L³ transversely and D/L in rotation, with
D = E h³ / 12(1 - ν²) the plate's bending stiffness and L its span across the
edge - its length L_x for the edges x = ±L_x/2, its width L_y for y = ±L_y/2.
That is the beam's rule (beamEndConditions) for a strip of plate one metre
wide, so the same factor serves.

Why 10^6 here too: a Rayleigh-Ritz model of the Table 5.1 plate, Legendre
polynomials with edge springs as in [BERRY 1991], put the first six natural
frequencies within 0.05 % (simply supported) and 0.09 % (clamped) of ideal
edges; 10^4 is still 3-6 % out. The same model gives 76.8 Hz for the first
simply supported mode, against 77.5 Hz from P.A.E.P. in Table 5.2.

Damping is the loss factor of springDamping, as on the beam.
"""

from __future__ import annotations

from dataclasses import replace
from enum import Enum

from activeControlBeamPlate.models.plateConfiguration import (
    EdgeSupport,
    PlateProperties,
    PlateSupports,
)
from activeControlBeamPlate.services.springDamping import damped, matches, sharedLossFactor

holdingFactor = 1e6
edges = ("edgeXNegative", "edgeXPositive", "edgeYNegative", "edgeYPositive")


class EdgeCondition(Enum):
    """Which motions of an edge are held: (transverse, rotation)."""

    free = ("Free", (False, False))
    simplySupported = ("Simply Supported", (True, False))
    clamped = ("Clamped", (True, True))

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def held(self) -> tuple[bool, bool]:
        return self.value[1]


conditionHelp = {
    EdgeCondition.free: "Nothing held: the edge moves and turns freely.",
    EdgeCondition.simplySupported: (
        "Held out of the plane, free to turn - the plate of Table 5.1."
    ),
    EdgeCondition.clamped: "Held in both ways: no movement, no turning.",
}


class EdgeConditionError(ValueError):
    """The plate's own values cannot give a stiffness to scale from."""


def span(plate: PlateProperties, edge: str) -> float:
    """The plate's span across `edge`, in m: its length for an x edge, its width for a y edge."""
    return (plate.length if edge.startswith("edgeX") else plate.width) / 1000


def plateStiffnesses(plate: PlateProperties, edge: str) -> tuple[float, float]:
    """The plate's own stiffness across `edge`, per metre of edge: (D/L³, D/L), SI units."""
    modulus, thickness, ratio = plate.youngsModulus.real, plate.thickness / 1000, plate.poissonRatio
    length = span(plate, edge)
    if min(modulus, thickness, length) <= 0 or not -1 < ratio < 0.5:
        raise EdgeConditionError(
            "The plate's length, width, thickness and Young's modulus must be greater than "
            "zero, and its Poisson's ratio between -1 and 0.5, to work out its edges."
        )
    rigidity = modulus * thickness**3 / (12 * (1 - ratio**2))
    return rigidity / length**3, rigidity / length


def recommendedReals(
    condition: EdgeCondition, plate: PlateProperties, edge: str
) -> tuple[float, float]:
    """The real parts `condition` puts on an edge's springs, for this plate."""
    references = plateStiffnesses(plate, edge)
    transverse, rotational = (
        holdingFactor * reference if held else 0.0
        for held, reference in zip(condition.held, references, strict=True)
    )
    return transverse, rotational


def springsOf(supports: PlateSupports, edge: str) -> tuple[complex, complex]:
    support: EdgeSupport = getattr(supports, edge)
    return complex(support.transverse), complex(support.rotational)


def lossFactorOf(supports: PlateSupports, edge: str) -> float | None:
    """The loss factor the edge's springs share; 0 with nothing held; None if they differ."""
    return sharedLossFactor(springsOf(supports, edge))


def conditionOf(
    supports: PlateSupports, edge: str, plate: PlateProperties
) -> EdgeCondition | None:
    """The condition whose recommended values the edge's real parts are, exactly; else None.

    Exactly, so a value changed by hand, or a plate made thicker, is no longer
    that condition. With no usable plate only Free can be recognised.
    """
    reals = [spring.real for spring in springsOf(supports, edge)]
    for condition in EdgeCondition:
        try:
            expected = recommendedReals(condition, plate, edge)
        except EdgeConditionError:
            if condition is not EdgeCondition.free:
                continue
            expected = (0.0, 0.0)
        if matches(reals, expected):
            return condition
    return None


def withCondition(
    supports: PlateSupports, edge: str, condition: EdgeCondition, plate: PlateProperties
) -> PlateSupports:
    """The edge set to `condition`, keeping its loss factor (0 if its springs had none)."""
    lossFactor = lossFactorOf(supports, edge) or 0.0
    transverse, rotational = recommendedReals(condition, plate, edge)
    return replace(supports, **{edge: EdgeSupport(
        transverse=complex(transverse, lossFactor * transverse),
        rotational=complex(rotational, lossFactor * rotational),
    )})


def withLossFactor(supports: PlateSupports, edge: str, lossFactor: float) -> PlateSupports:
    """The edge's springs damped by `lossFactor`: imaginary part = η × real part."""
    transverse, rotational = springsOf(supports, edge)
    return replace(supports, **{edge: EdgeSupport(
        transverse=damped(transverse, lossFactor), rotational=damped(rotational, lossFactor)
    )})

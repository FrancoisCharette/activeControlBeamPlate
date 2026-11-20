"""Typical end springs for a boundary condition, and damping as a loss factor.

The thesis models each end of the beam with three springs (equation 2.25) but
gives no values for them, so these are this app's recommendation, not the
thesis's.

A held motion gets a spring `holdingFactor` times stiffer than the beam itself
is for that motion - EI/L³ against transverse movement, EA/L against axial
movement, EI/L against rotation - from the beam's own length, width,
thickness and Young's modulus (real part) on the Parameters tab. A free
motion gets 0. Scaling to the beam keeps the recommendation right whatever
beam is typed in, where a fixed number would be rigid for one and soft for
another.

Why 10^6: a finite-element check on the beam of Table 2.2 put the first three
natural frequencies within 0.02 % (pinned) and 0.05 % (clamped) of ideal
supports; 10^4 is still 2-5 % out, and 10^8 gains little while making the
model's equations worse conditioned. The same check gives 345.7 Hz for the
second pinned mode, against the 339 Hz the thesis reports with A.C.P.A.,
which lowers frequencies by about 2 %.

Damping is a loss factor η: the imaginary part of each spring is η times its
real part, the convention of Table 2.2's complex moduli - the beam's
35.5e7 / 71e9 is η = 0.5 %.
"""

from __future__ import annotations

from dataclasses import replace
from enum import Enum

from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.models.beamMaterials import BeamMaterials
from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.services.springDamping import damped, matches, sharedLossFactor

holdingFactor = 1e6


class EndCondition(Enum):
    """Which motions of an end are held: (transverse, axial, rotation)."""

    free = ("Free", (False, False, False))
    pinned = ("Pinned", (True, True, False))
    roller = ("Roller", (True, False, False))
    clamped = ("Clamped", (True, True, True))

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def held(self) -> tuple[bool, bool, bool]:
        return self.value[1]


conditionHelp = {
    EndCondition.free: "Nothing held: the end moves and turns freely.",
    EndCondition.pinned: "Held up-and-down and along the beam; free to turn.",
    EndCondition.roller: (
        "Held up-and-down only; free to slide along the beam and to turn - the thesis's "
        "simply supported beam of Table 2.1, held transversely and free axially."
    ),
    EndCondition.clamped: "Held in every way: no movement, no turning.",
}
# The three springs of each end, in the order (transverse, axial, rotational).
endFields = {
    "left": ("transverseLeft", "axialLeft", "rotationalLeft"),
    "right": ("transverseRight", "axialRight", "rotationalRight"),
}


class EndConditionError(ValueError):
    """The beam's own values cannot give a stiffness to scale from."""


def beamStiffnesses(geometry: BeamGeometry, materials: BeamMaterials) -> tuple[float, ...]:
    """The beam's own stiffness against each motion: (EI/L³, EA/L, EI/L), in SI units."""
    modulus = materials.beamYoungsModulus.real
    length, width, thickness = (
        geometry.beamLength / 1000, geometry.width / 1000, geometry.beamThickness / 1000
    )
    if min(modulus, length, width, thickness) <= 0:
        raise EndConditionError(
            "The beam's length, width, thickness and Young's modulus must all be greater "
            "than zero to work out its supports."
        )
    area = width * thickness
    inertia = width * thickness**3 / 12
    return (
        modulus * inertia / length**3,
        modulus * area / length,
        modulus * inertia / length,
    )


def lossFactorOf(supports: BeamSupports, end: str) -> float | None:
    """The loss factor the end's springs share; 0 with nothing held; None if they differ."""
    return sharedLossFactor([getattr(supports, name) for name in endFields[end]])


def recommendedReals(
    condition: EndCondition, geometry: BeamGeometry, materials: BeamMaterials
) -> tuple[float, ...]:
    """The real parts `condition` puts on an end's springs, for this beam."""
    references = beamStiffnesses(geometry, materials)
    return tuple(
        holdingFactor * reference if held else 0.0
        for held, reference in zip(condition.held, references, strict=True)
    )


def conditionOf(
    supports: BeamSupports, end: str, geometry: BeamGeometry, materials: BeamMaterials
) -> EndCondition | None:
    """The condition whose recommended values the end's real parts are, exactly; else None.

    Exactly, so that changing any of them by hand - or changing the beam, which
    changes what the recommendation is - no longer counts as that condition.
    With no usable beam only Free, which needs none, can be recognised.
    """
    reals = [getattr(supports, name).real for name in endFields[end]]
    for condition in EndCondition:
        try:
            expected = recommendedReals(condition, geometry, materials)
        except EndConditionError:
            if condition is EndCondition.free:
                expected = (0.0, 0.0, 0.0)
            else:
                continue
        if matches(reals, expected):
            return condition
    return None


def withCondition(
    supports: BeamSupports,
    end: str,
    condition: EndCondition,
    geometry: BeamGeometry,
    materials: BeamMaterials,
) -> BeamSupports:
    """The end set to `condition`, keeping its loss factor (0 if its springs had none)."""
    lossFactor = lossFactorOf(supports, end) or 0.0
    reals = recommendedReals(condition, geometry, materials)
    return replace(supports, **{
        name: complex(real, lossFactor * real)
        for name, real in zip(endFields[end], reals, strict=True)
    })


def withLossFactor(supports: BeamSupports, end: str, lossFactor: float) -> BeamSupports:
    """The end's springs damped by `lossFactor`: imaginary part = η × real part."""
    return replace(supports, **{
        name: damped(getattr(supports, name), lossFactor) for name in endFields[end]
    })

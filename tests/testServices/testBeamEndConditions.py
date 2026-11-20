"""Tests for the recommended end springs and the loss-factor damping."""

from __future__ import annotations

from dataclasses import replace

import pytest

from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.models.beamMaterials import BeamMaterials
from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.services import beamEndConditions
from activeControlBeamPlate.services.beamEndConditions import (
    EndCondition,
    EndConditionError,
    conditionOf,
    holdingFactor,
    lossFactorOf,
    withCondition,
    withLossFactor,
)


def table22Stiffnesses() -> tuple[float, ...]:
    return beamEndConditions.beamStiffnesses(BeamGeometry(), BeamMaterials())


def testTheBeamsOwnStiffnessesAreWorkedOutFromItsSection() -> None:
    """Table 2.2's beam: 71e9 Pa, 12.65 x 3.25 mm, 295 mm long."""
    transverse, axial, rotational = table22Stiffnesses()
    inertia = 12.65e-3 * 3.25e-3**3 / 12

    assert transverse == pytest.approx(71e9 * inertia / 0.295**3)
    assert axial == pytest.approx(71e9 * 12.65e-3 * 3.25e-3 / 0.295)
    assert rotational == pytest.approx(71e9 * inertia / 0.295)
    assert transverse == pytest.approx(100.08, rel=1e-3)  # N/m


@pytest.mark.parametrize("condition, held", [
    (EndCondition.free, (False, False, False)),
    (EndCondition.pinned, (True, True, False)),
    (EndCondition.roller, (True, False, False)),
    (EndCondition.clamped, (True, True, True)),
])
def testEachConditionHoldsWhatItSays(condition: EndCondition, held: tuple[bool, ...]) -> None:
    supports = withCondition(BeamSupports(), "left", condition, BeamGeometry(), BeamMaterials())

    springs = (supports.transverseLeft, supports.axialLeft, supports.rotationalLeft)
    for spring, isHeld, reference in zip(springs, held, table22Stiffnesses(), strict=True):
        expected = holdingFactor * reference if isHeld else 0.0
        assert spring.real == pytest.approx(expected)
    # The other end is left alone.
    assert (supports.transverseRight, supports.axialRight, supports.rotationalRight) == (0, 0, 0)


def conditionOfLeft(supports: BeamSupports, geometry: BeamGeometry | None = None):
    return conditionOf(supports, "left", geometry or BeamGeometry(), BeamMaterials())


def testAConditionIsReadBackFromTheValuesItPutThere() -> None:
    for condition in EndCondition:
        supports = withCondition(BeamSupports(), "right", condition, BeamGeometry(),
                                 BeamMaterials())
        assert conditionOf(supports, "right", BeamGeometry(), BeamMaterials()) is condition


def testSpringsThatFitNoConditionAreNone() -> None:
    """Rotation held but not translation: not a support anybody builds."""
    supports = replace(BeamSupports(), rotationalLeft=5.0)

    assert conditionOfLeft(supports) is None


def testAnyChangeToARecommendedValueIsNoLongerThatCondition() -> None:
    """Still holding the same motions, but not the values the button put there."""
    clamped = withCondition(BeamSupports(), "left", EndCondition.clamped, BeamGeometry(),
                            BeamMaterials())

    for name in ("transverseLeft", "axialLeft", "rotationalLeft"):
        spring = getattr(clamped, name)
        changed = replace(clamped, **{name: complex(spring.real * 1.001, spring.imag)})
        assert conditionOfLeft(changed) is None, name
        # As it shows in the box: six significant digits typed back in.
        retyped = replace(clamped, **{name: complex(float(f"{spring.real:.6g}"), 0)})
        assert conditionOfLeft(retyped) is None, name


def testDampingDoesNotChangeWhichConditionItIs() -> None:
    pinned = withCondition(BeamSupports(), "left", EndCondition.pinned, BeamGeometry(),
                           BeamMaterials())

    assert conditionOfLeft(withLossFactor(pinned, "left", 0.05)) is EndCondition.pinned


def testChangingTheBeamChangesWhatTheConditionMeans() -> None:
    """Pinned for 295 mm is not pinned for 300 mm: the recommendation moved."""
    pinned = withCondition(BeamSupports(), "left", EndCondition.pinned, BeamGeometry(),
                           BeamMaterials())

    assert conditionOfLeft(pinned, replace(BeamGeometry(), beamLength=300.0)) is None


def testFreeIsRecognisedEvenWithNoUsableBeam() -> None:
    """Free needs no beam to scale from; the others cannot be checked without one."""
    noBeam = replace(BeamGeometry(), beamThickness=0.0)

    assert conditionOfLeft(BeamSupports(), noBeam) is EndCondition.free
    assert conditionOfLeft(replace(BeamSupports(), transverseLeft=1e8), noBeam) is None


def testTheRecommendationFollowsTheBeam() -> None:
    """Twice as long: EI/L³ falls eightfold, so the held transverse spring does too."""
    longer = replace(BeamGeometry(), beamLength=590.0)

    short = withCondition(BeamSupports(), "left", EndCondition.pinned, BeamGeometry(),
                          BeamMaterials())
    long = withCondition(BeamSupports(), "left", EndCondition.pinned, longer, BeamMaterials())

    assert long.transverseLeft.real == pytest.approx(short.transverseLeft.real / 8)


def testANonsenseBeamCannotGiveARecommendation() -> None:
    with pytest.raises(EndConditionError, match="must all be greater than zero"):
        withCondition(BeamSupports(), "left", EndCondition.clamped,
                      replace(BeamGeometry(), beamThickness=0.0), BeamMaterials())


def testDampingIsTheLossFactorTimesEachRealPart() -> None:
    clamped = withCondition(BeamSupports(), "left", EndCondition.clamped, BeamGeometry(),
                            BeamMaterials())

    damped = withLossFactor(clamped, "left", 0.02)

    for name in ("transverseLeft", "axialLeft", "rotationalLeft"):
        spring = getattr(damped, name)
        assert spring.real == getattr(clamped, name).real
        assert spring.imag == pytest.approx(0.02 * spring.real)
    assert lossFactorOf(damped, "left") == pytest.approx(0.02)


def testChangingTheConditionKeepsTheDamping() -> None:
    """Pick 1 % first, then Clamped: the new springs are damped at 1 % too."""
    pinned = withCondition(BeamSupports(), "left", EndCondition.pinned, BeamGeometry(),
                           BeamMaterials())
    damped = withLossFactor(pinned, "left", 0.01)

    clamped = withCondition(damped, "left", EndCondition.clamped, BeamGeometry(),
                            BeamMaterials())

    assert clamped.rotationalLeft.real > 0
    assert lossFactorOf(clamped, "left") == pytest.approx(0.01)


def testTheLossFactorIsNoneWhenTheSpringsDisagree() -> None:
    supports = replace(BeamSupports(), transverseLeft=100 + 1j, axialLeft=100 + 2j)

    assert lossFactorOf(supports, "left") is None


def testAFreeEndHasNoDamping() -> None:
    assert lossFactorOf(BeamSupports(), "left") == 0.0
    assert withLossFactor(BeamSupports(), "left", 0.05) == BeamSupports()


def testTheOfferedLevelsRunFromNoneToTenPercent() -> None:
    texts = [beamEndConditions.lossFactorText(level) for level in beamEndConditions.lossFactors]

    assert texts == ["0 %", "0.1 %", "0.2 %", "0.4 %", "0.8 %", "1 %", "2 %", "5 %", "10 %"]

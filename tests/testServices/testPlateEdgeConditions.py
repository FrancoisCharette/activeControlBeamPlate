"""Tests for the recommended plate edge springs and their damping."""

from __future__ import annotations

from dataclasses import replace

import pytest

from activeControlBeamPlate.models.plateConfiguration import (
    EdgeSupport,
    PlateProperties,
    PlateSupports,
)
from activeControlBeamPlate.services import plateEdgeConditions
from activeControlBeamPlate.services.plateEdgeConditions import (
    EdgeCondition,
    EdgeConditionError,
    conditionOf,
    holdingFactor,
    lossFactorOf,
    withCondition,
    withLossFactor,
)

plate = PlateProperties()  # Table 5.1
rigidity = 66.5e9 * 3.22e-3**3 / (12 * (1 - 0.33**2))


def testThePlatesOwnStiffnessIsTakenAcrossEachEdge() -> None:
    """x edges span the length, 480 mm; y edges the width, 420 mm."""
    for edge, span in (("edgeXNegative", 0.48), ("edgeXPositive", 0.48),
                       ("edgeYNegative", 0.42), ("edgeYPositive", 0.42)):
        transverse, rotational = plateEdgeConditions.plateStiffnesses(plate, edge)
        assert transverse == pytest.approx(rigidity / span**3)
        assert rotational == pytest.approx(rigidity / span)


@pytest.mark.parametrize("condition, held", [
    (EdgeCondition.free, (False, False)),
    (EdgeCondition.simplySupported, (True, False)),
    (EdgeCondition.clamped, (True, True)),
])
def testEachConditionHoldsWhatItSays(condition: EdgeCondition, held: tuple[bool, ...]) -> None:
    supports = withCondition(PlateSupports(), "edgeYNegative", condition, plate)

    edge = supports.edgeYNegative
    references = plateEdgeConditions.plateStiffnesses(plate, "edgeYNegative")
    for spring, isHeld, reference in zip((edge.transverse, edge.rotational), held, references,
                                         strict=True):
        assert complex(spring).real == pytest.approx(holdingFactor * reference if isHeld else 0)
    # The other edges are left alone.
    assert supports.edgeXNegative == EdgeSupport()


def testAConditionIsReadBackFromTheValuesItPutThere() -> None:
    for condition in EdgeCondition:
        supports = withCondition(PlateSupports(), "edgeXPositive", condition, plate)
        assert conditionOf(supports, "edgeXPositive", plate) is condition


def testAnyChangeToARecommendedValueIsNoLongerThatCondition() -> None:
    clamped = withCondition(PlateSupports(), "edgeXNegative", EdgeCondition.clamped, plate)
    edge = clamped.edgeXNegative

    nudged = replace(clamped, edgeXNegative=replace(edge, rotational=edge.rotational * 1.001))

    assert conditionOf(nudged, "edgeXNegative", plate) is None


def testChangingThePlateChangesWhatTheConditionMeans() -> None:
    supported = withCondition(PlateSupports(), "edgeXNegative",
                              EdgeCondition.simplySupported, plate)

    assert conditionOf(supported, "edgeXNegative", replace(plate, thickness=3.0)) is None
    # The width does not enter an x edge's stiffness, so it stays recognised.
    assert conditionOf(supported, "edgeXNegative", replace(plate, width=400.0)) is (
        EdgeCondition.simplySupported
    )


def testANonsensePlateCannotGiveARecommendation() -> None:
    with pytest.raises(EdgeConditionError, match="must be greater than zero"):
        withCondition(PlateSupports(), "edgeXNegative", EdgeCondition.clamped,
                      replace(plate, thickness=0.0))


def testFreeIsRecognisedEvenWithNoUsablePlate() -> None:
    noPlate = replace(plate, thickness=0.0)

    assert conditionOf(PlateSupports(), "edgeYPositive", noPlate) is EdgeCondition.free


def testDampingIsTheLossFactorTimesEachRealPart() -> None:
    clamped = withCondition(PlateSupports(), "edgeYPositive", EdgeCondition.clamped, plate)

    damped = withLossFactor(clamped, "edgeYPositive", 0.02)

    for spring in (damped.edgeYPositive.transverse, damped.edgeYPositive.rotational):
        assert spring.imag == pytest.approx(0.02 * spring.real)
    assert lossFactorOf(damped, "edgeYPositive") == pytest.approx(0.02)
    assert conditionOf(damped, "edgeYPositive", plate) is EdgeCondition.clamped


def testChangingTheConditionKeepsTheDamping() -> None:
    supported = withCondition(PlateSupports(), "edgeXNegative",
                              EdgeCondition.simplySupported, plate)
    damped = withLossFactor(supported, "edgeXNegative", 0.01)

    clamped = withCondition(damped, "edgeXNegative", EdgeCondition.clamped, plate)

    assert lossFactorOf(clamped, "edgeXNegative") == pytest.approx(0.01)


def testAPlainNumberInAnEdgeSpringIsReadAsComplex() -> None:
    """EdgeSupport(rotational=3.5): no damping, a loss factor of 0."""
    supports = replace(PlateSupports(), edgeXNegative=EdgeSupport(rotational=3.5))

    assert lossFactorOf(supports, "edgeXNegative") == 0.0

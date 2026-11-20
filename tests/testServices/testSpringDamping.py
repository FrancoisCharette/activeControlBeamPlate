"""Tests for the loss-factor damping shared by the beam's ends and the plate's edges."""

from __future__ import annotations

from activeControlBeamPlate.services.springDamping import (
    damped,
    lossFactors,
    lossFactorText,
    matches,
    offeredLevel,
    sharedLossFactor,
)


def testTheOfferedLevelsRunFromNoneToTenPercent() -> None:
    assert [lossFactorText(level) for level in lossFactors] == [
        "0 %", "0.1 %", "0.2 %", "0.4 %", "0.8 %", "1 %", "2 %", "5 %", "10 %"
    ]


def testTheSharedLossFactorSkipsSpringsWithNoStiffness() -> None:
    assert sharedLossFactor([100 + 2j, 0j, 50 + 1j]) == 0.02
    assert sharedLossFactor([0j, 0j]) == 0.0


def testSpringsThatDisagreeShareNoLossFactor() -> None:
    assert sharedLossFactor([100 + 1j, 100 + 2j]) is None
    assert sharedLossFactor([0 + 1j]) is None  # damping with no stiffness


def testOnlyAnOfferedLevelIsNamed() -> None:
    assert offeredLevel(0.01) == 0.01
    assert offeredLevel(0.015) is None
    assert offeredLevel(None) is None


def testDampingKeepsTheRealPart() -> None:
    assert damped(200 + 9j, 0.05) == 200 + 10j


def testMatchingIsExactUpToRounding() -> None:
    assert matches([1e8, 0.0], [1e8 * (1 + 1e-12), 0.0])
    assert not matches([1e8, 0.0], [1.0001e8, 0.0])
    assert not matches([1e-3, 0.0], [0.0, 0.0])

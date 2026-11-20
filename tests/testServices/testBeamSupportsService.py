"""Tests for the end springs of the beam of Figure 2.1: the checks and what is kept."""

from __future__ import annotations

from dataclasses import replace

from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.services import beamSupportsService, settingsService


def testTheDefaultIsAFreeFreeBeam() -> None:
    """Every spring 0: the condition of the experiments on the beam of Table 2.2."""
    supports = BeamSupports()

    assert all(getattr(supports, name) == 0 for name in BeamSupports.fieldNames())
    assert len(BeamSupports.fieldNames()) == 6


def testPassiveSpringsHaveNoProblems() -> None:
    supports = replace(BeamSupports(), transverseLeft=1e12 + 1e9j, rotationalRight=50.0)

    assert beamSupportsService.problemsWith(supports) == []


def testANegativeStiffnessOrDampingIsNamedWithItsSpring() -> None:
    supports = replace(BeamSupports(), axialLeft=-5.0, rotationalRight=10 - 2j)

    assert beamSupportsService.problemsWith(supports) == [
        "The stiffness of the left axial spring, K_H1 cannot be negative.",
        "The damping of the right rotational spring, K_T2 cannot be negative.",
    ]


def testNothingSavedMeansFreeEnds() -> None:
    assert beamSupportsService.loadSupports() == BeamSupports()


def testTheSpringsComeBackAsSavedRealAndImaginary() -> None:
    supports = BeamSupports(
        transverseLeft=1e12 + 3e8j,
        axialLeft=2.5e6,
        rotationalLeft=1j,
        transverseRight=7.0,
        axialRight=0j,
        rotationalRight=125.5 + 0.5j,
    )

    beamSupportsService.saveSupports(supports)

    assert beamSupportsService.loadSupports() == supports


def testAnUnreadablePartFallsBackToZeroForThatPartOnly() -> None:
    beamSupportsService.saveSupports(replace(BeamSupports(), transverseLeft=100 + 4j))
    settingsService.writeValue(f"{beamSupportsService.settingsGroup}/transverseLeft/imag", "x")

    assert beamSupportsService.loadSupports().transverseLeft == 100 + 0j

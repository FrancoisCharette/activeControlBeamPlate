"""Tests for the beam dimensions of Figure 2.1: the checks and what is kept."""

from __future__ import annotations

from dataclasses import replace

from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.services import beamGeometryService, settingsService


def testTheDefaultsAreTable22() -> None:
    """The configuration chapter 2 uses throughout, in millimetres."""
    assert BeamGeometry() == BeamGeometry(
        beamLength=295.0,
        width=12.65,
        beamThickness=3.25,
        actuatorLength=25.38,
        actuatorThickness=0.18,
        actuatorPosition=131.0,
        sensorLength=295.0,
        sensorThickness=0.11,
        sensorPosition=0.0,
    )


def testTable22DescribesABuildableBeam() -> None:
    """Including the sensor, which ends exactly at both ends of the beam."""
    assert beamGeometryService.problemsWith(BeamGeometry()) == []


def testATransducerMayTouchEitherEnd() -> None:
    atLeftEnd = replace(BeamGeometry(), actuatorPosition=-(295.0 - 25.38) / 2)

    assert beamGeometryService.problemsWith(atLeftEnd) == []


def testAnActuatorPastTheEndIsNamedWithWhereItIs() -> None:
    geometry = replace(BeamGeometry(), actuatorPosition=140.0)

    problems = beamGeometryService.problemsWith(geometry)

    assert len(problems) == 1
    assert "actuator runs past the end of the beam" in problems[0]
    assert "127.31 to 152.69 mm" in problems[0]
    assert "-147.5 to 147.5 mm" in problems[0]


def testASensorLongerThanTheBeamIsCaught() -> None:
    geometry = replace(BeamGeometry(), sensorLength=300.0)

    problems = beamGeometryService.problemsWith(geometry)

    assert len(problems) == 1 and problems[0].startswith("The sensor runs past")


def testANegativePositionPastTheLeftEndIsCaught() -> None:
    geometry = replace(BeamGeometry(), actuatorPosition=-140.0)

    assert "actuator runs past" in beamGeometryService.problemsWith(geometry)[0]


def testALengthOfZeroIsCaughtOnceAndNotAsRunningPastTheEnd() -> None:
    geometry = replace(BeamGeometry(), actuatorLength=0.0)

    assert beamGeometryService.problemsWith(geometry) == [
        "The actuator length must be greater than zero."
    ]


def testAWidthOrThicknessOfZeroIsCaught() -> None:
    geometry = replace(BeamGeometry(), width=0.0, sensorThickness=0.0)

    assert beamGeometryService.problemsWith(geometry) == [
        "The width must be greater than zero.",
        "The sensor thickness must be greater than zero.",
    ]


def testWithNoBeamOnlyTheLengthIsReported() -> None:
    """Nothing can fit on a beam of no length, so saying so for each transducer is noise."""
    geometry = replace(BeamGeometry(), beamLength=0.0)

    assert beamGeometryService.problemsWith(geometry) == [
        "The beam length must be greater than zero."
    ]


def testNothingSavedMeansTable22() -> None:
    assert beamGeometryService.loadGeometry() == BeamGeometry()


def testTheDimensionsComeBackAsSaved() -> None:
    geometry = BeamGeometry(
        beamLength=400.0,
        width=20.0,
        beamThickness=2.5,
        actuatorLength=50.5,
        actuatorThickness=0.25,
        actuatorPosition=-120.25,
        sensorLength=100.0,
        sensorPosition=30.0,
    )

    beamGeometryService.saveGeometry(geometry)

    assert beamGeometryService.loadGeometry() == geometry


def testWhatIsKeptIsWhatWasTypedEvenIfItCannotBeBuilt() -> None:
    geometry = replace(BeamGeometry(), sensorLength=500.0)

    beamGeometryService.saveGeometry(geometry)

    assert beamGeometryService.loadGeometry() == geometry


def testAnUnreadableSavedValueFallsBackToTable22ForThatValueOnly() -> None:
    beamGeometryService.saveGeometry(replace(BeamGeometry(), beamLength=400.0))
    settingsService.writeValue(f"{beamGeometryService.settingsGroup}/actuatorLength", "long")

    geometry = beamGeometryService.loadGeometry()

    assert geometry.actuatorLength == BeamGeometry().actuatorLength
    assert geometry.beamLength == 400.0

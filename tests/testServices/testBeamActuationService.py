"""Tests for how the beam is driven: the checks and what is kept."""

from __future__ import annotations

from dataclasses import replace

from activeControlBeamPlate.models.beamActuation import BeamActuation, Excitation
from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.services import beamActuationService, settingsService
from activeControlBeamPlate.services.beamActuationService import frequencyCount, problemsWith

table22 = BeamGeometry()
# A sensor clear of the actuator at 131 mm: x = -145 to 5 mm.
clearSensor = replace(table22, sensorLength=150.0, sensorPosition=-70.0)


def testTheDefaultsAreTheThesissDrive() -> None:
    """Asymmetric as Table 2.2's beam; 1 V at 0° as section 4.4; chapter 2's 3200 Hz."""
    assert BeamActuation() == BeamActuation(
        excitation=Excitation.asymmetric,
        voltageAmplitude=1.0,
        voltagePhase=0.0,
        frequencyStart=1.0,
        frequencyEnd=3200.0,
        frequencyStep=1.0,
    )
    assert problemsWith(BeamActuation(), table22) == []


def testTheSymmetricExcitationsDriveTheLowerElementAsTheThesisSays() -> None:
    assert Excitation.asymmetric.lowerPhaseShift is None
    assert Excitation.pureBending.lowerPhaseShift == 180.0
    assert Excitation.pureExtension.lowerPhaseShift == 0.0
    assert [excitation.isSymmetric for excitation in Excitation] == [False, True, True]


def testTheBandCountsBothEnds() -> None:
    assert frequencyCount(BeamActuation()) == 3200
    assert frequencyCount(replace(BeamActuation(), frequencyStart=0.0, frequencyEnd=10.0,
                                  frequencyStep=2.5)) == 5
    # 0.1 does not divide 1 exactly in binary; the end is still counted.
    assert frequencyCount(replace(BeamActuation(), frequencyStart=0.0, frequencyEnd=1.0,
                                  frequencyStep=0.1)) == 11


def testABandThatHoldsNothingIsCaught() -> None:
    backwards = replace(BeamActuation(), frequencyStart=500.0, frequencyEnd=100.0)
    noStep = replace(BeamActuation(), frequencyStep=0.0)

    assert problemsWith(backwards, table22) == [
        "The end of the frequency band must be above its start."
    ]
    assert problemsWith(noStep, table22) == ["The frequency step must be greater than zero."]
    assert frequencyCount(backwards) == 0 and frequencyCount(noStep) == 0


def testAMistypedTinyStepIsCaught() -> None:
    tiny = replace(BeamActuation(), frequencyStep=0.001)

    problems = problemsWith(tiny, table22)

    assert len(problems) == 1 and "use a larger step" in problems[0]


def testNoVoltageIsCaught() -> None:
    assert problemsWith(replace(BeamActuation(), voltageAmplitude=0.0), table22) == [
        "The voltage amplitude must be greater than zero."
    ]


def testASymmetricExcitationCannotSitOnTheSensor() -> None:
    """Table 2.2's sensor covers the whole lower surface: no room for a lower actuator."""
    for excitation in (Excitation.pureBending, Excitation.pureExtension):
        problems = problemsWith(replace(BeamActuation(), excitation=excitation), table22)
        assert len(problems) == 1
        assert "where the sensor is (x = -147.5 to 147.5 mm)" in problems[0]
        assert problemsWith(replace(BeamActuation(), excitation=excitation), clearSensor) == []


def testAnAsymmetricExcitationDoesNotCareWhereTheSensorIs() -> None:
    assert problemsWith(BeamActuation(), table22) == []


def testNothingSavedMeansTheDefaults() -> None:
    assert beamActuationService.loadActuation() == BeamActuation()


def testTheActuationComesBackAsSaved() -> None:
    actuation = BeamActuation(Excitation.pureExtension, 60.0, -90.0, 10.0, 2000.0, 0.5)

    beamActuationService.saveActuation(actuation)

    assert beamActuationService.loadActuation() == actuation


def testAnUnknownSavedExcitationFallsBackToAsymmetric() -> None:
    beamActuationService.saveActuation(replace(BeamActuation(), voltageAmplitude=5.0))
    settingsService.writeValue(f"{beamActuationService.settingsGroup}/excitation", "twisting")

    actuation = beamActuationService.loadActuation()

    assert actuation.excitation is Excitation.asymmetric
    assert actuation.voltageAmplitude == 5.0

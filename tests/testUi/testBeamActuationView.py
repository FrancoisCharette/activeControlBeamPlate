"""Tests for the Beam > Actuation tab."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QGroupBox

from activeControlBeamPlate.models.beamActuation import BeamActuation, Excitation
from activeControlBeamPlate.services import beamActuationService
from activeControlBeamPlate.ui.beam.beamActuationView import BeamActuationView
from activeControlBeamPlate.ui.beam.beamView import BeamView


def newView(qtbot) -> BeamActuationView:
    view = BeamActuationView()
    qtbot.addWidget(view)
    return view


def testItHasTheExcitationTheVoltageAndTheBand(qtbot) -> None:
    view = newView(qtbot)

    groups = [box.title() for box in view.findChildren(QGroupBox)]
    assert groups == ["Excitation", "Applied Voltage", "Frequency Band"]
    assert [button.text() for button in view.excitationButtons.values()] == [
        "Asymmetric", "Symmetric, Pure Bending", "Symmetric, Pure Extension"
    ]
    assert list(view.inputs) == [
        "voltageAmplitude", "voltagePhase", "frequencyStart", "frequencyEnd", "frequencyStep"
    ]
    assert view.inputs["voltageAmplitude"].suffix() == " V"
    assert view.inputs["frequencyEnd"].suffix() == " Hz"


def testItOpensOnTheDefaultsTheFirstTime(qtbot) -> None:
    view = newView(qtbot)
    view.show()

    assert view.actuation() == BeamActuation()
    assert view.excitationButtons[Excitation.asymmetric].isChecked()
    assert view.countLabel.text() == "3,200 frequencies, from 1 Hz."
    assert not view.problemLabel.isVisible()


def testItOpensOnWhatWasLastChosen(qtbot) -> None:
    saved = BeamActuation(Excitation.pureBending, 60.0, 90.0, 0.0, 1600.0, 2.0)
    beamActuationService.saveActuation(saved)

    view = newView(qtbot)

    assert view.actuation() == saved
    assert view.excitationButtons[Excitation.pureBending].isChecked()


def testAChangeIsKeptAndAnnounced(qtbot) -> None:
    view = newView(qtbot)
    announced: list[BeamActuation] = []
    view.actuationChanged.connect(announced.append)

    view.inputs["voltageAmplitude"].setValue(60.0)
    view.excitationButtons[Excitation.pureExtension].click()

    expected = replace(BeamActuation(), voltageAmplitude=60.0,
                       excitation=Excitation.pureExtension)
    assert announced[-1] == expected
    assert beamActuationService.loadActuation() == expected


def testTheCountFollowsTheBand(qtbot) -> None:
    view = newView(qtbot)

    view.inputs["frequencyStep"].setValue(2.0)

    assert view.countLabel.text() == "1,600 frequencies, from 1 Hz."


def testASymmetricExcitationOnTable22sSensorIsExplained(qtbot) -> None:
    view = newView(qtbot)
    view.show()

    view.excitationButtons[Excitation.pureBending].click()

    assert view.problemLabel.isVisible()
    assert "where the sensor is" in view.problemLabel.text()


def testTheSensorCheckFollowsTheParametersTab(qtbot) -> None:
    """Shorten the sensor on Configuration > Parameters and the problem goes away."""
    beam = BeamView()
    qtbot.addWidget(beam)
    beam.show()
    actuation = beam.actuationView
    parameters = beam.configurationView.parametersView
    beam.tabs.setCurrentWidget(actuation)
    actuation.excitationButtons[Excitation.pureBending].click()
    assert actuation.problemLabel.isVisible()

    parameters.inputs["sensorLength"].setValue(150.0)
    parameters.inputs["sensorPosition"].setValue(-70.0)

    assert not actuation.problemLabel.isVisible()


def testRestoreBringsBackTheDefaults(qtbot) -> None:
    view = newView(qtbot)
    view.excitationButtons[Excitation.pureBending].click()
    view.inputs["frequencyEnd"].setValue(800.0)
    statuses: list[str] = []
    view.statusMessage.connect(statuses.append)

    view.restoreButton.click()

    assert view.actuation() == BeamActuation()
    assert beamActuationService.loadActuation() == BeamActuation()
    assert statuses == ["Beam actuation set to the default values."]


def testItIsTheActuationTabOfTheBeam(qtbot) -> None:
    beam = BeamView()
    qtbot.addWidget(beam)

    assert isinstance(beam.actuationView, BeamActuationView)
    assert beam.tabs.widget(1) is beam.actuationView

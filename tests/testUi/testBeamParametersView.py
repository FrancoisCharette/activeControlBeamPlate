"""Tests for the Beam > Configuration > Parameters tab: the dimensions of Figure 2.1."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QGroupBox, QLabel

from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.services import beamGeometryService, beamSupportsService
from activeControlBeamPlate.ui.beam.beamConfigurationView import BeamConfigurationView
from activeControlBeamPlate.ui.beam.beamParametersView import BeamParametersView


def newView(qtbot) -> BeamParametersView:
    view = BeamParametersView()
    qtbot.addWidget(view)
    return view


def testThereIsAnInputForEveryDimensionInTheFigure(qtbot) -> None:
    view = newView(qtbot)

    assert sorted(view.inputs) == sorted(BeamGeometry.fieldNames())
    assert sorted(view.supportsBox.inputs) == sorted(BeamSupports.fieldNames())
    labels = " ".join(label.text() for label in view.findChildren(QLabel))
    for symbol in ("L<sub>x</sub><sup>pt</sup>", "L<sub>x</sub><sup>a</sup>",
                   "x<sub>a</sub>", "L<sub>x</sub><sup>c</sup>", "x<sub>c</sub>",
                   "L<sub>y</sub>", "L<sub>z</sub><sup>pt</sup>", "L<sub>z</sub><sup>a</sup>",
                   "L<sub>z</sub><sup>c</sup>"):
        assert symbol in labels
    for end in "12":
        for kind in "VHT":
            assert f"K<sub>{kind}{end}</sub>" in labels
    assert all(spinBox.suffix() == " mm" for spinBox in view.inputs.values())


def testTheInputsAreGroupedByThePartTheyBelongTo(qtbot) -> None:
    view = newView(qtbot)

    groups = {box.title(): box for box in view.findChildren(QGroupBox)}

    assert list(groups) == ["Beam", "Actuator", "Sensor", "End Supports"]
    assert view.inputs["width"].parent() is groups["Beam"]
    assert view.inputs["actuatorThickness"].parent() is groups["Actuator"]
    assert view.inputs["actuatorPosition"].parent() is groups["Actuator"]
    assert view.inputs["sensorLength"].parent() is groups["Sensor"]


def testItOpensOnTable22TheFirstTime(qtbot) -> None:
    view = newView(qtbot)
    view.show()

    assert view.geometry() == BeamGeometry()
    assert view.supports() == BeamSupports()  # free-free, as in the experiments
    assert not view.problemLabel.isVisible()


def testItOpensOnWhatWasLastTyped(qtbot) -> None:
    saved = replace(BeamGeometry(), beamLength=400.0, actuatorPosition=-50.0)
    beamGeometryService.saveGeometry(saved)
    springs = replace(BeamSupports(), transverseLeft=1e12 + 5e9j, rotationalRight=25.0)
    beamSupportsService.saveSupports(springs)

    view = newView(qtbot)

    assert view.geometry() == saved
    assert view.supports() == springs


def testOnlyPositionsCanBeNegative(qtbot) -> None:
    view = newView(qtbot)

    for field, spinBox in view.inputs.items():
        assert (spinBox.minimum() < 0) == field.endswith("Position")


def testAChangeIsKeptAndAnnounced(qtbot) -> None:
    view = newView(qtbot)
    announced: list[BeamGeometry] = []
    view.geometryChanged.connect(announced.append)

    view.inputs["beamLength"].setValue(350.0)

    expected = replace(BeamGeometry(), beamLength=350.0)
    assert announced == [expected]
    assert beamGeometryService.loadGeometry() == expected


def testAnImpossibleBeamIsExplainedUnderTheInputs(qtbot) -> None:
    view = newView(qtbot)
    view.show()

    view.inputs["actuatorPosition"].setValue(140.0)

    assert view.problemLabel.isVisible()
    assert "actuator runs past the end of the beam" in view.problemLabel.text()

    view.inputs["actuatorPosition"].setValue(100.0)

    assert not view.problemLabel.isVisible()


def testRestoreBringsBackTable22(qtbot) -> None:
    view = newView(qtbot)
    view.show()
    view.inputs["sensorLength"].setValue(500.0)
    view.inputs["actuatorLength"].setValue(10.0)
    view.supportsBox.inputs["axialRight"][0].setValue(3e6)
    statuses: list[str] = []
    view.statusMessage.connect(statuses.append)

    view.restoreButton.click()

    assert view.geometry() == BeamGeometry()
    assert view.supports() == BeamSupports()
    assert beamGeometryService.loadGeometry() == BeamGeometry()
    assert beamSupportsService.loadSupports() == BeamSupports()
    assert not view.problemLabel.isVisible()
    assert statuses == ["Beam parameters set to Table 2.2, with free ends."]


def testItIsTheParametersTabOfTheBeamConfiguration(qtbot) -> None:
    configuration = BeamConfigurationView()
    qtbot.addWidget(configuration)

    assert isinstance(configuration.parametersView, BeamParametersView)
    assert configuration.tabs.widget(1) is configuration.parametersView


def testAChangedSpringIsKeptAndAnnounced(qtbot) -> None:
    view = newView(qtbot)
    announced: list[BeamSupports] = []
    view.supportsChanged.connect(announced.append)
    real, imaginary = view.supportsBox.inputs["transverseLeft"]

    real.setValue(1e12)
    imaginary.setValue(2e9)

    expected = replace(BeamSupports(), transverseLeft=1e12 + 2e9j)
    assert announced[-1] == expected
    assert beamSupportsService.loadSupports() == expected


def testTheSpringsCannotBeTypedNegative(qtbot) -> None:
    """A negative stiffness or damping is not a support, so the boxes stop at 0."""
    view = newView(qtbot)

    for real, imaginary in view.supportsBox.inputs.values():
        assert real.minimum() == 0 and imaginary.minimum() == 0


def testTheUnitsMatchWhatEachSpringResists(qtbot) -> None:
    """Equation 2.25: K_V and K_H against a displacement, K_T against a rotation."""
    view = newView(qtbot)
    labels = [label.text() for label in view.supportsBox.findChildren(QLabel)]

    assert labels.count("N/m") == 4
    assert labels.count("N·m/rad") == 2

"""Tests for the Beam > Configuration > Parameters tab: the dimensions of Figure 2.1."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QGroupBox, QLabel

from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.models.beamMaterials import BeamMaterials
from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.services import (
    beamGeometryService,
    beamMaterialsService,
    beamSupportsService,
)
from activeControlBeamPlate.services.flatValues import flatten
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

    assert list(groups) == ["Beam", "Actuator", "Sensor", "Materials", "End Supports"]
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
    view.materialsBox.inputs["sensorDensity"].setValue(1780.0)
    statuses: list[str] = []
    view.statusMessage.connect(statuses.append)

    view.restoreButton.click()

    assert view.geometry() == BeamGeometry()
    assert view.materials() == BeamMaterials()
    assert view.supports() == BeamSupports()
    assert beamGeometryService.loadGeometry() == BeamGeometry()
    assert beamMaterialsService.loadMaterials() == BeamMaterials()
    assert beamSupportsService.loadSupports() == BeamSupports()
    assert not view.problemLabel.isVisible()
    assert statuses == ["Beam parameters set to Table 2.2, with free ends."]


def testItIsTheParametersTabOfTheBeamConfiguration(qtbot) -> None:
    configuration = BeamConfigurationView()
    qtbot.addWidget(configuration)

    assert isinstance(configuration.parametersView, BeamParametersView)
    assert configuration.tabs.widget(0) is configuration.parametersView


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


def testThereIsAMaterialInputForEveryValueOfTable22AndNoOther(qtbot) -> None:
    view = newView(qtbot)

    assert sorted(view.materialsBox.inputs) == sorted(flatten(BeamMaterials()))


def testItShowsTable22sMaterialsExactly(qtbot) -> None:
    """Unrounded and unclipped - 190e-12 and 71e9 among them."""
    view = newView(qtbot)
    view.show()

    assert view.materials() == BeamMaterials()
    for path, value in flatten(BeamMaterials()).items():
        assert view.materialsBox.inputs[path].value() == value, path
    assert not view.problemLabel.isVisible()


def testWhatAPartDoesNotHaveIsADash(qtbot) -> None:
    """The beam is not piezoelectric; only the sensor's permittivity is in Table 2.2."""
    view = newView(qtbot)
    inputs = view.materialsBox.inputs

    assert "beamDzx" not in inputs and "beamEzx" not in inputs
    assert "actuatorPermittivity" not in inputs and "beamPermittivity" not in inputs
    assert [label.text() for label in view.materialsBox.findChildren(QLabel)].count("-") == 4


def testAChangedMaterialIsKeptAndAnnounced(qtbot) -> None:
    view = newView(qtbot)
    announced: list[BeamMaterials] = []
    view.materialsChanged.connect(announced.append)

    view.materialsBox.inputs["beamYoungsModulus/imag"].setValue(1e9)

    expected = replace(BeamMaterials(), beamYoungsModulus=71e9 + 1e9j)
    assert announced == [expected]
    assert beamMaterialsService.loadMaterials() == expected


def testAMaterialProblemIsExplainedUnderTheInputs(qtbot) -> None:
    view = newView(qtbot)
    view.show()

    view.materialsBox.inputs["sensorPermittivity"].setValue(0.0)

    assert "sensor permittivity must be greater than zero" in view.problemLabel.text()


def testItOpensOnTheMaterialsLastTyped(qtbot) -> None:
    saved = replace(BeamMaterials(), actuatorDzx=-171e-12, sensorEzx=0.05)
    beamMaterialsService.saveMaterials(saved)

    view = newView(qtbot)

    assert view.materials() == saved


def menuAction(button, text: str):
    return next(action for action in button.menu().actions() if action.text() == text)


def testEachEndHasAConditionAndADampingButton(qtbot) -> None:
    view = newView(qtbot)
    box = view.supportsBox

    for end in ("left", "right"):
        conditions = [action.text() for action in box.conditionButtons[end].menu().actions()]
        assert conditions == ["Free", "Pinned", "Roller", "Clamped"]
        levels = [action.text() for action in box.dampingButtons[end].menu().actions()]
        assert levels[:7] == ["0 %", "0.1 %", "0.2 %", "0.4 %", "0.8 %", "1 %", "2 %"]
        # Free ends with no damping, as Table 2.2's experiments were.
        assert box.conditionButtons[end].text() == "Condition: Free"
        assert box.dampingButtons[end].text() == "Damping: 0 %"


def testChoosingAConditionFillsTheRealPartsAndIsKept(qtbot) -> None:
    view = newView(qtbot)
    box = view.supportsBox
    statuses: list[str] = []
    view.statusMessage.connect(statuses.append)

    menuAction(box.conditionButtons["left"], "Clamped").trigger()

    supports = view.supports()
    assert all(spring.real > 0 for spring in
               (supports.transverseLeft, supports.axialLeft, supports.rotationalLeft))
    assert supports.transverseRight == 0
    assert beamSupportsService.loadSupports() == supports
    assert box.conditionButtons["left"].text() == "Condition: Clamped"
    assert statuses[-1] == "Left end set to Clamped."


def testChoosingADampingFillsTheImaginaryParts(qtbot) -> None:
    view = newView(qtbot)
    box = view.supportsBox
    menuAction(box.conditionButtons["right"], "Pinned").trigger()

    menuAction(box.dampingButtons["right"], "2 %").trigger()

    supports = view.supports()
    assert supports.transverseRight.imag == supports.transverseRight.real * 0.02
    assert supports.axialRight.imag == supports.axialRight.real * 0.02
    assert supports.rotationalRight == 0  # free to turn, so nothing to damp
    assert box.dampingButtons["right"].text() == "Damping: 2 %"
    assert beamSupportsService.loadSupports() == supports


def testTypingAValueByHandShowsCustom(qtbot) -> None:
    view = newView(qtbot)
    box = view.supportsBox
    real, imaginary = box.inputs["rotationalLeft"]

    real.setValue(10.0)
    imaginary.setValue(3.0)

    assert box.conditionButtons["left"].text() == "Condition: Custom"
    assert box.dampingButtons["left"].text() == "Damping: Custom"


def testEditingARecommendedValueByHandShowsCustom(qtbot) -> None:
    """Like Damping: the Condition names a support only while its values are untouched."""
    view = newView(qtbot)
    box = view.supportsBox
    menuAction(box.conditionButtons["left"], "Clamped").trigger()
    real, _imaginary = box.inputs["axialLeft"]

    real.setValue(real.value() * 2)

    assert box.conditionButtons["left"].text() == "Condition: Custom"
    assert box.conditionButtons["right"].text() == "Condition: Free"

    menuAction(box.conditionButtons["left"], "Clamped").trigger()

    assert box.conditionButtons["left"].text() == "Condition: Clamped"


def testTypingTheDisplayedValueBackInIsCustom(qtbot) -> None:
    """The box shows six significant digits; typed back, that is not the exact value."""
    view = newView(qtbot)
    box = view.supportsBox
    menuAction(box.conditionButtons["right"], "Pinned").trigger()
    real, _imaginary = box.inputs["transverseRight"]

    real.setValue(float(real.text()))

    assert box.conditionButtons["right"].text() == "Condition: Custom"


def testChangingTheBeamTurnsAChosenConditionToCustom(qtbot) -> None:
    """The recommendation is scaled to the beam, so a longer beam needs choosing again."""
    view = newView(qtbot)
    box = view.supportsBox
    menuAction(box.conditionButtons["left"], "Pinned").trigger()

    view.inputs["beamLength"].setValue(300.0)

    assert box.conditionButtons["left"].text() == "Condition: Custom"

    view.inputs["beamLength"].setValue(295.0)

    assert box.conditionButtons["left"].text() == "Condition: Pinned"


def testChangingTheBeamsModulusTurnsAChosenConditionToCustom(qtbot) -> None:
    view = newView(qtbot)
    box = view.supportsBox
    menuAction(box.conditionButtons["right"], "Clamped").trigger()

    view.materialsBox.inputs["beamYoungsModulus/real"].setValue(70e9)

    assert box.conditionButtons["right"].text() == "Condition: Custom"


def testAChosenConditionIsRecognisedAfterARestart(qtbot) -> None:
    """Saved and read back, the values are still exactly the recommended ones."""
    first = newView(qtbot)
    menuAction(first.supportsBox.conditionButtons["left"], "Clamped").trigger()

    second = newView(qtbot)

    assert second.supportsBox.conditionButtons["left"].text() == "Condition: Clamped"


def testAConditionNeedsABeamToScaleFrom(qtbot) -> None:
    """With no thickness there is no beam stiffness: nothing changes, and the bar says why."""
    view = newView(qtbot)
    view.inputs["beamThickness"].setValue(0.0)
    statuses: list[str] = []
    view.statusMessage.connect(statuses.append)

    menuAction(view.supportsBox.conditionButtons["left"], "Pinned").trigger()

    assert view.supports() == BeamSupports()
    assert "must all be greater than zero" in statuses[-1]

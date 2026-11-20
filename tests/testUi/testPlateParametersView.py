"""Tests for the Plate > Configuration > Parameters tab: Figure 5.1 and Table 5.1."""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import QGroupBox, QLabel

from activeControlBeamPlate.models.plateConfiguration import (
    EdgeSupport,
    PlateConfiguration,
    PlateSupports,
)
from activeControlBeamPlate.services import plateConfigurationService
from activeControlBeamPlate.services.flatValues import flatten
from activeControlBeamPlate.ui.plate.plateConfigurationView import PlateConfigurationView
from activeControlBeamPlate.ui.plate.plateParametersView import PlateParametersView


def newView(qtbot) -> PlateParametersView:
    view = PlateParametersView()
    qtbot.addWidget(view)
    return view


def testThereIsAnInputForEveryValueAndNoOther(qtbot) -> None:
    view = newView(qtbot)

    assert sorted(view.inputs) == sorted(flatten(PlateConfiguration()))


def testItShowsTable51ExactlyTheFirstTime(qtbot) -> None:
    """Every value, unrounded and unclipped: a Young's modulus of 63e9 once came back
    as 1e5, because its input had the range of a length."""
    view = newView(qtbot)
    view.show()

    assert view.configuration() == PlateConfiguration()
    for path, value in flatten(PlateConfiguration()).items():
        assert view.inputs[path].value() == value, path
    assert not view.problemLabel.isVisible()


def testItIsLaidOutLikeTable51(qtbot) -> None:
    view = newView(qtbot)
    labels = [label.text() for label in view.findChildren(QLabel)]

    for title in ("<b>Primary Actuator</b>", "<b>Secondary Actuator</b>", "<b>Plate</b>"):
        assert title in labels
    for symbol in ("L<sub>x</sub>", "L<sub>y</sub>", "L<sub>z</sub>", "ρ", "ν",
                   "e<sub>zx</sub>", "d<sub>zx</sub>", "x<sub>a</sub>", "y<sub>a</sub>"):
        assert any(symbol in label for label in labels), symbol
    # The piezoelectric and position rows are the actuators' alone.
    assert "plate/positionX" not in view.inputs
    assert "plate/dzx" not in view.inputs
    groups = [box.title() for box in view.findChildren(QGroupBox)]
    assert groups == ["Plate and Actuators", "Edge Supports"]


def testEveryEdgeHasATransverseAndARotationalSpring(qtbot) -> None:
    view = newView(qtbot)

    for edge in ("edgeXNegative", "edgeXPositive", "edgeYNegative", "edgeYPositive"):
        for kind in ("transverse", "rotational"):
            for part in ("real", "imag"):
                spinBox = view.inputs[f"supports/{edge}/{kind}/{part}"]
                assert spinBox.minimum() == 0


def testItOpensOnWhatWasLastTyped(qtbot) -> None:
    saved = replace(
        PlateConfiguration(),
        supports=replace(PlateSupports(), edgeXPositive=EdgeSupport(transverse=1e12)),
    )
    plateConfigurationService.saveConfiguration(saved)

    view = newView(qtbot)

    assert view.configuration() == saved


def testAChangeIsKeptAndAnnounced(qtbot) -> None:
    view = newView(qtbot)
    announced: list[PlateConfiguration] = []
    view.configurationChanged.connect(announced.append)

    view.inputs["secondaryActuator/positionX"].setValue(100.0)

    expected = PlateConfiguration()
    expected = replace(expected, secondaryActuator=replace(expected.secondaryActuator,
                                                           positionX=100.0))
    assert announced == [expected]
    assert plateConfigurationService.loadConfiguration() == expected


def testAnImpossiblePlateIsExplainedUnderTheInputs(qtbot) -> None:
    view = newView(qtbot)
    view.show()

    view.inputs["primaryActuator/positionY"].setValue(200.0)

    assert view.problemLabel.isVisible()
    assert "primary actuator runs past the edge of the plate in y" in view.problemLabel.text()


def testRestoreBringsBackTable51(qtbot) -> None:
    view = newView(qtbot)
    view.show()
    view.inputs["plate/length"].setValue(10.0)
    view.inputs["supports/edgeYNegative/rotational/real"].setValue(5.0)
    statuses: list[str] = []
    view.statusMessage.connect(statuses.append)

    view.restoreButton.click()

    assert view.configuration() == PlateConfiguration()
    assert plateConfigurationService.loadConfiguration() == PlateConfiguration()
    assert not view.problemLabel.isVisible()
    assert statuses == ["Plate parameters set to Table 5.1, with free edges."]


def testItIsTheParametersTabOfThePlateConfiguration(qtbot) -> None:
    configuration = PlateConfigurationView()
    qtbot.addWidget(configuration)

    assert isinstance(configuration.parametersView, PlateParametersView)
    assert configuration.tabs.widget(0) is configuration.parametersView


def menuAction(button, text: str):
    return next(action for action in button.menu().actions() if action.text() == text)


edgeKeys = ("edgeXNegative", "edgeXPositive", "edgeYNegative", "edgeYPositive")


def testEachEdgeAndAllEdgesHaveAConditionAndADampingButton(qtbot) -> None:
    view = newView(qtbot)
    box = view.edgesBox

    for key in ("all", *edgeKeys):
        conditions = [action.text() for action in box.conditionButtons[key].menu().actions()]
        assert conditions == ["Free", "Simply Supported", "Clamped"]
        levels = [action.text() for action in box.dampingButtons[key].menu().actions()]
        assert levels[:7] == ["0 %", "0.1 %", "0.2 %", "0.4 %", "0.8 %", "1 %", "2 %"]
        assert box.conditionButtons[key].text() == "Condition: Free"
        assert box.dampingButtons[key].text() == "Damping: 0 %"


def testAllEdgesSetsTheFourAndIsKept(qtbot) -> None:
    view = newView(qtbot)
    box = view.edgesBox
    statuses: list[str] = []
    view.statusMessage.connect(statuses.append)

    menuAction(box.conditionButtons["all"], "Simply Supported").trigger()

    supports = view.configuration().supports
    for key in edgeKeys:
        edge = getattr(supports, key)
        assert edge.transverse.real > 0 and edge.rotational == 0
        assert box.conditionButtons[key].text() == "Condition: Simply Supported"
    assert box.conditionButtons["all"].text() == "Condition: Simply Supported"
    assert plateConfigurationService.loadConfiguration().supports == supports
    assert statuses[-1] == "All edges set to Simply Supported."


def testOneEdgeAloneMakesAllEdgesMixed(qtbot) -> None:
    view = newView(qtbot)
    box = view.edgesBox
    menuAction(box.conditionButtons["all"], "Clamped").trigger()

    menuAction(box.dampingButtons["edgeYPositive"], "1 %").trigger()

    edge = view.configuration().supports.edgeYPositive
    assert edge.transverse.imag == edge.transverse.real * 0.01
    assert box.dampingButtons["edgeYPositive"].text() == "Damping: 1 %"
    assert box.dampingButtons["all"].text() == "Damping: Mixed"
    assert box.conditionButtons["all"].text() == "Condition: Clamped"


def testEditingAValueByHandShowsCustom(qtbot) -> None:
    view = newView(qtbot)
    box = view.edgesBox
    menuAction(box.conditionButtons["edgeXNegative"], "Clamped").trigger()

    view.inputs["supports/edgeXNegative/rotational/real"].setValue(5.0)

    assert box.conditionButtons["edgeXNegative"].text() == "Condition: Custom"
    assert box.conditionButtons["all"].text() == "Condition: Mixed"


def testChangingThePlateTurnsAChosenConditionToCustom(qtbot) -> None:
    view = newView(qtbot)
    box = view.edgesBox
    menuAction(box.conditionButtons["all"], "Simply Supported").trigger()

    view.inputs["plate/thickness"].setValue(3.0)

    assert all(box.conditionButtons[key].text() == "Condition: Custom" for key in edgeKeys)


def testAChosenConditionIsRecognisedAfterARestart(qtbot) -> None:
    first = newView(qtbot)
    menuAction(first.edgesBox.conditionButtons["all"], "Clamped").trigger()

    second = newView(qtbot)

    assert second.edgesBox.conditionButtons["all"].text() == "Condition: Clamped"


def testAConditionNeedsAPlateToScaleFrom(qtbot) -> None:
    view = newView(qtbot)
    view.inputs["plate/thickness"].setValue(0.0)
    statuses: list[str] = []
    view.statusMessage.connect(statuses.append)

    menuAction(view.edgesBox.conditionButtons["all"], "Clamped").trigger()

    assert view.configuration().supports == PlateSupports()
    assert "must be greater than zero" in statuses[-1]

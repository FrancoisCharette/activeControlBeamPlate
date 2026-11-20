"""Tests for the tabs under Beam and Plate: Configuration (Schematic, Parameters),
Actuation and Sensing."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QTabWidget

from activeControlBeamPlate.ui.beam.beamActuationView import BeamActuationView
from activeControlBeamPlate.ui.beam.beamConfigurationView import BeamConfigurationView
from activeControlBeamPlate.ui.beam.beamParametersView import BeamParametersView
from activeControlBeamPlate.ui.beam.beamSchematicView import BeamSchematicView
from activeControlBeamPlate.ui.beam.beamSensingView import BeamSensingView
from activeControlBeamPlate.ui.beam.beamView import BeamView
from activeControlBeamPlate.ui.plate.plateActuationView import PlateActuationView
from activeControlBeamPlate.ui.plate.plateConfigurationView import PlateConfigurationView
from activeControlBeamPlate.ui.plate.plateParametersView import PlateParametersView
from activeControlBeamPlate.ui.plate.plateSchematicView import PlateSchematicView
from activeControlBeamPlate.ui.plate.plateSensingView import PlateSensingView
from activeControlBeamPlate.ui.plate.plateView import PlateView
from activeControlBeamPlate.ui.widgets.fullWidthTabWidget import FullWidthTabWidget
from activeControlBeamPlate.ui.widgets.reportingView import ReportingView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView

structures = [
    pytest.param(
        BeamView, "beam",
        (BeamConfigurationView, BeamActuationView, BeamSensingView), id="beam",
    ),
    pytest.param(
        PlateView, "plate",
        (PlateConfigurationView, PlateActuationView, PlateSensingView), id="plate",
    ),
]


@pytest.mark.parametrize(("viewClass", "name", "pageClasses"), structures)
def testItHasConfigurationActuationAndSensingInThatOrder(
    qtbot, viewClass, name: str, pageClasses
) -> None:
    view = viewClass()
    qtbot.addWidget(view)

    assert view.pageTitles() == ["Configuration", "Actuation", "Sensing"]
    pages = [view.configurationView, view.actuationView, view.sensingView]
    assert [view.tabs.widget(index) for index in range(3)] == pages
    assert [type(page) for page in pages] == list(pageClasses)
    assert view.tabs.currentWidget() is view.configurationView


@pytest.mark.parametrize(("viewClass", "name", "pageClasses"), structures)
def testItsTabControlIsHighlighted(qtbot, viewClass, name: str, pageClasses) -> None:
    view = viewClass()
    qtbot.addWidget(view)

    assert isinstance(view.tabs, FullWidthTabWidget)
    assert all(isinstance(control, FullWidthTabWidget)
               for control in view.findChildren(QTabWidget))


@pytest.mark.parametrize(("viewClass", "name", "pageClasses"), structures)
def testActuationAndSensingSayTheyAreEmptyAndCanTakeChildTabs(
    qtbot, viewClass, name: str, pageClasses
) -> None:
    view = viewClass()
    qtbot.addWidget(view)
    view.show()

    for page in (view.actuationView, view.sensingView):
        view.tabs.setCurrentWidget(page)
        assert isinstance(page, TabbedView)
        assert page.pageTitles() == []
        assert page.emptyLabel.isVisible()
        assert name in page.emptyLabel.text().lower()


@pytest.mark.parametrize(("viewClass", "name", "pageClasses"), structures)
def testReportsFromASecondLevelTabReachTheStructure(
    qtbot, viewClass, name: str, pageClasses
) -> None:
    view = viewClass()
    qtbot.addWidget(view)
    page = ReportingView()
    view.sensingView.addPage("Sensor", page)
    messages: list[str] = []
    view.statusMessage.connect(messages.append)

    page.reportStatus("Reading sensors...")

    assert messages == ["Reading sensors..."]


configurations = [
    pytest.param(BeamView, "beam", (BeamSchematicView, BeamParametersView), id="beam"),
    pytest.param(PlateView, "plate", (PlateSchematicView, PlateParametersView), id="plate"),
]


@pytest.mark.parametrize(("viewClass", "name", "pageClasses"), configurations)
def testConfigurationHasSchematicThenParameters(qtbot, viewClass, name: str, pageClasses) -> None:
    view = viewClass()
    qtbot.addWidget(view)
    configuration = view.configurationView

    assert configuration.pageTitles() == ["Schematic", "Parameters"]
    pages = [configuration.schematicView, configuration.parametersView]
    assert [configuration.tabs.widget(index) for index in range(2)] == pages
    assert [type(page) for page in pages] == list(pageClasses)
    assert configuration.tabs.currentWidget() is configuration.schematicView
    assert isinstance(configuration.tabs, FullWidthTabWidget)
    assert configuration.tabs.styleSheet() == view.tabs.styleSheet()

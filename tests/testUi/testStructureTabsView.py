"""Tests for the window's top-level switch, Beam / Plate."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.beam.beamView import BeamView
from activeControlBeamPlate.ui.plate.plateView import PlateView
from activeControlBeamPlate.ui.structureTabsView import StructureTabsView
from activeControlBeamPlate.ui.widgets.fullWidthTabWidget import FullWidthTabWidget
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


def testItOffersBeamThenPlate(qtbot) -> None:
    view = StructureTabsView()
    qtbot.addWidget(view)

    assert view.pageTitles() == ["Beam", "Plate"]


def testItOpensOnBeam(qtbot) -> None:
    view = StructureTabsView()
    qtbot.addWidget(view)

    assert view.tabs.currentWidget() is view.beamView


def testEachStructureIsATabbedView(qtbot) -> None:
    view = StructureTabsView()
    qtbot.addWidget(view)

    assert isinstance(view.beamView, BeamView)
    assert isinstance(view.plateView, PlateView)
    assert view.tabs.widget(0) is view.beamView
    assert view.tabs.widget(1) is view.plateView
    for structure in (view.beamView, view.plateView):
        assert isinstance(structure, TabbedView)


def testBothStructuresShowTheirSecondLevelTabs(qtbot) -> None:
    view = StructureTabsView()
    qtbot.addWidget(view)
    view.show()

    assert view.beamView.tabs.isVisible()
    assert not view.beamView.emptyLabel.isVisible()

    view.tabs.setCurrentWidget(view.plateView)

    assert view.plateView.tabs.isVisible()
    assert not view.plateView.emptyLabel.isVisible()


def testAChildTabAddedUnderASecondLevelTabIsHighlighted(qtbot) -> None:
    """The next step of the app, done the way README.md describes it."""
    view = StructureTabsView()
    qtbot.addWidget(view)
    view.show()
    actuation = view.beamView.actuationView
    view.beamView.tabs.setCurrentWidget(actuation)

    actuation.addPage("Sample Actuator", QWidget())

    assert actuation.pageTitles() == ["Sample Actuator"]
    assert actuation.tabs.isVisible()
    assert not actuation.emptyLabel.isVisible()
    assert isinstance(actuation.tabs, FullWidthTabWidget)
    assert actuation.tabs.styleSheet() == view.tabs.styleSheet()
    # The same tab under the other structure is untouched.
    assert view.plateView.actuationView.pageTitles() == []


def testTheSwitchRunsEdgeToEdgeAndChildControlsAreSetIn(qtbot) -> None:
    view = StructureTabsView()
    qtbot.addWidget(view)

    assert view.layout().contentsMargins().isNull()
    assert not view.beamView.layout().contentsMargins().isNull()

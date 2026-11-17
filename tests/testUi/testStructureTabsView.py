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


def testEachStructureIsAViewReadyForChildTabs(qtbot) -> None:
    view = StructureTabsView()
    qtbot.addWidget(view)

    assert isinstance(view.beamView, BeamView)
    assert isinstance(view.plateView, PlateView)
    assert view.tabs.widget(0) is view.beamView
    assert view.tabs.widget(1) is view.plateView
    for structure in (view.beamView, view.plateView):
        assert isinstance(structure, TabbedView)


def testAStructureWithNoConfigurationSaysSo(qtbot) -> None:
    view = StructureTabsView()
    qtbot.addWidget(view)
    view.show()

    assert view.beamView.emptyLabel.isVisible()
    assert "beam" in view.beamView.emptyLabel.text().lower()
    assert "plate" in view.plateView.emptyLabel.text().lower()
    assert view.beamView.pageTitles() == []
    assert view.plateView.pageTitles() == []


def testAConfigurationAddedToAStructureBecomesAHighlightedChildTab(qtbot) -> None:
    """The next step of the app, done the way README.md describes it."""
    view = StructureTabsView()
    qtbot.addWidget(view)
    view.show()

    view.beamView.addPage("Sample Configuration", QWidget())

    assert view.beamView.pageTitles() == ["Sample Configuration"]
    assert view.beamView.tabs.isVisible()
    assert not view.beamView.emptyLabel.isVisible()
    assert isinstance(view.beamView.tabs, FullWidthTabWidget)
    assert view.beamView.tabs.styleSheet() == view.tabs.styleSheet()
    # The other structure is untouched.
    assert view.plateView.pageTitles() == []


def testTheSwitchRunsEdgeToEdgeAndChildControlsAreSetIn(qtbot) -> None:
    view = StructureTabsView()
    qtbot.addWidget(view)

    assert view.layout().contentsMargins().isNull()
    assert not view.beamView.layout().contentsMargins().isNull()

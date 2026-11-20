"""Tests for the tabbed view the app is built from."""

from __future__ import annotations

from PySide6.QtWidgets import QTabWidget, QWidget

from activeControlBeamPlate.ui.widgets.fullWidthTabWidget import FullWidthTabWidget
from activeControlBeamPlate.ui.widgets.reportingView import ReportingView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView

longFailure = (
    "The model did not converge. The usual cause is a mesh too coarse for the "
    "highest mode asked for, so refine it and run again."
)


def threeLevels(qtbot) -> tuple[TabbedView, TabbedView, TabbedView, ReportingView]:
    """A structure, a configuration under it, a variant under that, and a page at the bottom."""
    structure = TabbedView()
    qtbot.addWidget(structure)
    configuration = TabbedView()
    variant = TabbedView()
    page = ReportingView()
    variant.addPage("Page", page)
    configuration.addPage("Variant", variant)
    structure.addPage("Configuration", configuration)
    return structure, configuration, variant, page


def testItSaysWhatIsMissingUntilItHasAPage(qtbot) -> None:
    """An empty tab control is a bare frame, which reads as something broken."""
    view = TabbedView(emptyText="Nothing has been added yet.")
    qtbot.addWidget(view)
    view.show()

    assert view.emptyLabel.isVisible()
    assert view.emptyLabel.text() == "Nothing has been added yet."
    assert not view.tabs.isVisible()
    assert view.pageTitles() == []


def testTheFirstPageBringsTheTabsIn(qtbot) -> None:
    view = TabbedView(emptyText="Nothing has been added yet.")
    qtbot.addWidget(view)
    view.show()

    view.addPage("First", QWidget())

    assert view.tabs.isVisible()
    assert not view.emptyLabel.isVisible()


def testPagesKeepTheOrderTheyWereAddedIn(qtbot) -> None:
    view = TabbedView()
    qtbot.addWidget(view)
    first, second, third = QWidget(), QWidget(), QWidget()

    view.addPage("First", first)
    view.addPage("Second", second)
    view.addPage("Third", third)

    assert view.pageTitles() == ["First", "Second", "Third"]
    assert [view.tabs.widget(index) for index in range(3)] == [first, second, third]
    assert view.tabs.currentWidget() is first


def testItsTabControlIsTheHighlightedOne(qtbot) -> None:
    view = TabbedView()
    qtbot.addWidget(view)

    assert isinstance(view.tabs, FullWidthTabWidget)


def testEveryLevelOfANestIsHighlighted(qtbot) -> None:
    """The rule for the whole app, held by the base class rather than by each view."""
    structure, _configuration, _variant, _page = threeLevels(qtbot)

    controls = structure.findChildren(QTabWidget)

    assert len(controls) == 3
    assert all(isinstance(control, FullWidthTabWidget) for control in controls)
    assert len({control.styleSheet() for control in controls}) == 1
    assert all(control.property("highlightedTabs") is True for control in controls)


def testAPageReportsThroughTheViewHoldingIt(qtbot) -> None:
    view = TabbedView()
    qtbot.addWidget(view)
    page = ReportingView()
    view.addPage("Page", page)
    messages: list[str] = []
    errors: list[tuple[str, str]] = []
    view.statusMessage.connect(messages.append)
    view.errorMessage.connect(lambda title, message: errors.append((title, message)))

    page.reportStatus("Solving...")
    page.reportError("Model", longFailure)

    # The bar's headline and the dialog's whole text, exactly as the page sent them.
    assert messages == ["Solving...", "The model did not converge."]
    assert errors == [("Model", longFailure)]


def testReportsClimbEveryLevel(qtbot) -> None:
    """A page three tabs down is heard at the top, with nothing wired by hand."""
    structure, _configuration, _variant, page = threeLevels(qtbot)
    messages: list[str] = []
    errors: list[tuple[str, str]] = []
    structure.statusMessage.connect(messages.append)
    structure.errorMessage.connect(lambda title, message: errors.append((title, message)))

    page.reportStatus("Solving...")
    page.reportError("Model", longFailure)

    assert messages == ["Solving...", "The model did not converge."]
    assert errors == [("Model", longFailure)]


def testAViewStillReportsForItself(qtbot) -> None:
    """Passing its pages on does not cost a tabbed view its own voice."""
    view = TabbedView()
    qtbot.addWidget(view)
    messages: list[str] = []
    view.statusMessage.connect(messages.append)

    view.reportStatus("Three configurations loaded.")

    assert messages == ["Three configurations loaded."]


def testAPlainWidgetCanBeAPage(qtbot) -> None:
    """Not every page has something to report."""
    view = TabbedView()
    qtbot.addWidget(view)

    view.addPage("Plain", QWidget())

    assert view.pageTitles() == ["Plain"]


def twoBranches(qtbot) -> TabbedView:
    """Beam and Plate, each with three tabs of its own, like the app."""
    root = TabbedView()
    qtbot.addWidget(root)
    for structure in ("Beam", "Plate"):
        branch = TabbedView()
        for part in ("Configuration", "Actuation", "Sensing"):
            branch.addPage(part, TabbedView())
        root.addPage(structure, branch)
    return root


def branch(view: TabbedView, title: str) -> TabbedView:
    return dict(view.nestedViews())[title]


def testOpenTabsNamesTheOpenTabAtEveryLevel(qtbot) -> None:
    """Every branch, not only the one on screen, so each keeps its own choice."""
    root = twoBranches(qtbot)
    root.tabs.setCurrentIndex(1)
    branch(root, "Beam").tabs.setCurrentIndex(1)
    branch(root, "Plate").tabs.setCurrentIndex(2)

    # Empty third-level views have no tabs, so they have nothing to name.
    assert root.openTabs() == {"": "Plate", "Beam": "Actuation", "Plate": "Sensing"}


def testRestoringOpensTheSameTabsInAFreshTree(qtbot) -> None:
    first = twoBranches(qtbot)
    first.tabs.setCurrentIndex(1)
    branch(first, "Beam").tabs.setCurrentIndex(2)
    branch(first, "Plate").tabs.setCurrentIndex(1)

    second = twoBranches(qtbot)
    second.restoreOpenTabs(first.openTabs())

    assert second.openTabs() == first.openTabs()
    assert second.tabs.currentWidget() is branch(second, "Plate")


def testATitleThatNoLongerExistsLeavesThatLevelAsItIs(qtbot) -> None:
    """A tab renamed or removed since the last session must not break the rest."""
    root = twoBranches(qtbot)

    root.restoreOpenTabs({"": "Shell", "Beam": "Control Law", "Plate": "Sensing"})

    assert root.openTabs() == {"": "Beam", "Beam": "Configuration", "Plate": "Sensing"}


def testDeeperLevelsAreRestoredToo(qtbot) -> None:
    root = twoBranches(qtbot)
    actuation = branch(branch(root, "Beam"), "Actuation")
    actuation.addPage("One", QWidget())
    actuation.addPage("Two", QWidget())

    root.restoreOpenTabs({"Beam/Actuation": "Two"})

    assert actuation.tabs.currentIndex() == 1
    assert root.openTabs()["Beam/Actuation"] == "Two"

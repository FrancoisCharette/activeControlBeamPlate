"""A view made of tabs, each holding another view - the app's building block.

The app is a tree of these. The window's Beam / Plate switch is one, each of
its pages is one, and a page of those can be one again, for as many levels as
a configuration needs. Growing the app is adding a page; README.md has the
steps.

Two things are settled here so that no page has to think about them:

- the tab control is always the highlighted one, so every level shows which
  tab is open the same way;
- what a page reports is passed on to whatever holds this view, so status and
  failures reach the window from any depth through its one connectView call;
- which tab is open at every level can be read and set back as a whole, so
  the window can reopen where it was left without knowing the tree's shape.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from activeControlBeamPlate.services.windowStateService import tabPath
from activeControlBeamPlate.ui.widgets.fullWidthTabWidget import FullWidthTabWidget
from activeControlBeamPlate.ui.widgets.reportingView import ReportingView


class TabbedView(ReportingView):
    """A highlighted tab control whose pages are views, nestable to any depth."""

    def __init__(self, emptyText: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tabs = FullWidthTabWidget()
        # Stands in for the tab control until there is a page to put in it: a
        # control with no tabs is an empty frame that looks like a fault.
        self.emptyLabel = QLabel(emptyText)
        self.emptyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.emptyLabel.setWordWrap(True)
        self.emptyLabel.setForegroundRole(QPalette.ColorRole.PlaceholderText)

        # The layout keeps its margins, so a child control sits inside its
        # parent's page rather than hard against the tabs above it.
        layout = QVBoxLayout(self)
        layout.addWidget(self.emptyLabel)
        layout.addWidget(self.tabs)
        self.tabs.hide()

    def addPage(self, title: str, page: QWidget) -> None:
        """Add a tab holding `page`, after the ones already there.

        A page that is a view - anything from ReportingView, another
        TabbedView included - has its status and failures passed on, so it is
        never connected to the window by hand.
        """
        self.tabs.addTab(page, title)
        if isinstance(page, ReportingView):
            page.statusMessage.connect(self.statusMessage)
            page.errorMessage.connect(self.errorMessage)
        self.emptyLabel.hide()
        self.tabs.show()

    def pageTitles(self) -> list[str]:
        """The tab labels, left to right."""
        return [self.tabs.tabText(index) for index in range(self.tabs.count())]

    def nestedViews(self) -> list[tuple[str, TabbedView]]:
        """The tabbed views directly in this view's pages, with their tab titles."""
        pages = (self.tabs.widget(index) for index in range(self.tabs.count()))
        return [(title, page) for title, page in zip(self.pageTitles(), pages, strict=True)
                if isinstance(page, TabbedView)]

    def openTabs(self, path: str = "") -> dict[str, str]:
        """The open tab of this control and of every control beneath it, by place.

        Every level is included, not only the one on screen, so each branch
        remembers its own choice: Beam keeps Actuation open while Plate is shown.
        """
        state: dict[str, str] = {}
        if self.tabs.count():
            state[path] = self.tabs.tabText(self.tabs.currentIndex())
        for title, view in self.nestedViews():
            state.update(view.openTabs(tabPath(path, title)))
        return state

    def restoreOpenTabs(self, state: dict[str, str], path: str = "") -> None:
        """Open the saved tab at every level; a title that no longer exists is left as is."""
        title = state.get(path)
        if title in self.pageTitles():
            self.tabs.setCurrentIndex(self.pageTitles().index(title))
        for childTitle, view in self.nestedViews():
            view.restoreOpenTabs(state, tabPath(path, childTitle))

"""A view made of tabs, each holding another view - the app's building block.

The app is a tree of these. The window's Beam / Plate switch is one, each of
its pages is one, and a page of those can be one again, for as many levels as
a configuration needs. Growing the app is adding a page; README.md has the
steps.

Two things are settled here so that no page has to think about them:

- the tab control is always the highlighted one, so every level shows which
  tab is open the same way;
- what a page reports is passed on to whatever holds this view, so status and
  failures reach the window from any depth through its one connectView call.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

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

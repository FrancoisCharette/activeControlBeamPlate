"""The app's tab control: tabs share the full width equally, and the open one is marked.

Every tab control in the app is one of these, whatever its depth - the Beam /
Plate switch and each child control inside a page - so every level shows which
tab is open the same way, as 26wagerBook does: labels larger than the rest of
the interface, and an accent bar along the top of the open tab. How a tab is
marked, and why the colours come from the palette, is in tabStyling.

Views do not build one directly; they inherit TabbedView, which owns it.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QFont, QPalette, QResizeEvent
from PySide6.QtWidgets import QApplication, QTabBar, QTabWidget, QWidget

from activeControlBeamPlate.ui.widgets.tabStyling import styleKey, tabStyleSheet

labelScale = 1.15  # of the interface's own text size
accentBar = 3  # px of accent along the top of the open tab
padding = "5px 10px"
# The scope of this style, so nothing else in the window takes it. Scoped on a
# property, not the object name, which a view may set. Every level carries the
# same property and is given the same rules, so a child control looks the same
# whether Qt reads the rule from its own style sheet or from the control it
# sits in.
scope = 'QTabWidget[highlightedTabs="true"]'


class FullWidthTabBar(QTabBar):
    def tabSizeHint(self, index: int) -> QSize:
        size = super().tabSizeHint(index)
        tabWidget = self.parentWidget()
        if self.count() and tabWidget is not None:
            size.setWidth(tabWidget.width() // self.count())
        return size


class FullWidthTabWidget(QTabWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTabBar(FullWidthTabBar(self))
        self.setProperty("highlightedTabs", True)
        font = QFont()
        font.setPointSizeF(font.pointSizeF() * labelScale)
        font.setWeight(QFont.Weight.DemiBold)
        self.tabBar().setFont(font)
        self.styledFor: tuple[str, str] | None = None
        self.applyTheme()
        application = QApplication.instance()
        if application is not None:
            # Deprecated in Qt 6 but still the one signal that carries the new
            # palette; a test fails loudly if a future PySide6 drops it.
            application.paletteChanged.connect(self.onPaletteChanged)

    def onPaletteChanged(self, *_args: object) -> None:
        self.applyTheme()
        # Once more after Qt has finished handing the new palette round the
        # window: the re-inherit in applyTheme must come after that hand-off.
        QTimer.singleShot(0, self, self.reinheritPalette)

    def applyTheme(self, *_args: object) -> None:
        """Set the open tab apart, and join it to the page it belongs to."""
        self.reinheritPalette()
        built = styleKey(self)
        if built == self.styledFor:
            return
        self.styledFor = built
        self.setStyleSheet(tabStyleSheet(self, scope, accentBar, padding))

    def reinheritPalette(self) -> None:
        """A Qt quirk, seen in Qt 6.12 with no app code involved.

        A tab widget inside another widget stops taking palette changes once
        its tabs carry a style sheet, so after Help > Theme > Light whatever
        sat under it stayed dark in an otherwise light window. An empty palette
        tells it to inherit from its parent again; it fixes nothing in place,
        so the next switch is inherited the same way.
        """
        self.setPalette(QPalette())

    def resizeEvent(self, event: QResizeEvent) -> None:
        # Tab widths derive from the widget width, so a resize must make the
        # tab bar re-query its size hints. QTabBar has no public relayout;
        # re-setting the icon size is the standard way to force one.
        super().resizeEvent(event)
        tabBar = self.tabBar()
        tabBar.setIconSize(tabBar.iconSize())

"""Tests for the app's tab control, and how it shows which tab is open - at any depth."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette, QStandardItemModel
from PySide6.QtWidgets import QTableView, QVBoxLayout, QWidget

from activeControlBeamPlate.ui import tabTheme
from activeControlBeamPlate.ui.widgets import fullWidthTabWidget, tabStyling
from activeControlBeamPlate.ui.widgets.fullWidthTabWidget import FullWidthTabWidget


def tabsFillHalves(tabWidget: FullWidthTabWidget) -> bool:
    tabBar = tabWidget.tabBar()
    share = tabWidget.width() // tabBar.count()
    return all(
        abs(tabBar.tabRect(i).width() - share) <= 1 for i in range(tabBar.count())
    )


def rule(style: str, selector: str) -> str:
    """What one rule of a stylesheet declares."""
    return style.split(selector, 1)[1].split("}", 1)[0]


def withTabs(qtbot, *titles: str) -> FullWidthTabWidget:
    tabWidget = FullWidthTabWidget()
    qtbot.addWidget(tabWidget)
    for title in titles or ("First", "Second"):
        tabWidget.addTab(QWidget(), title)
    return tabWidget


def childControlInAPage(
    childFirst: bool = False,
) -> tuple[FullWidthTabWidget, FullWidthTabWidget, QTableView]:
    """A tab control in a page of another, with a table under both.

    `childFirst` builds the child before its parent, the order a view built
    ahead of the control it is added to produces. The caller hands qtbot
    whichever widget ends up outermost, and nothing inside it.
    """
    child = FullWidthTabWidget() if childFirst else None
    parent = FullWidthTabWidget()
    child = child or FullWidthTabWidget()
    table = QTableView()
    table.setModel(QStandardItemModel(2, 2))
    child.addTab(table, "Child One")
    child.addTab(QWidget(), "Child Two")
    page = QWidget()
    QVBoxLayout(page).addWidget(child)
    parent.addTab(page, "Parent One")
    parent.addTab(QWidget(), "Parent Two")
    return parent, child, table


def accentIsPaintedOn(tabWidget: FullWidthTabWidget, index: int) -> bool:
    """Whether the accent bar is really drawn along the top of a tab.

    Read from the pixels, because a style sheet being set says nothing about
    whether Qt applied it to this control.
    """
    tabBar = tabWidget.tabBar()
    image = tabBar.grab().toImage()
    ratio = image.devicePixelRatio()
    tab = tabBar.tabRect(index)
    page, _ink = tabStyling.pageAndInk(tabWidget)
    accent = QColor(tabTheme.accentFor(page)).name()
    x = round(tab.center().x() * ratio)
    top = max(round(tab.top() * ratio), 0)
    bottom = min(top + round((fullWidthTabWidget.accentBar + 2) * ratio), image.height())
    return any(image.pixelColor(x, y).name() == accent for y in range(top, bottom))


def testTabsShareWidthEqually(qtbot) -> None:
    tabWidget = withTabs(qtbot)
    tabWidget.resize(600, 400)
    tabWidget.show()

    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)


def testTabsKeepEqualShareAfterResize(qtbot) -> None:
    tabWidget = withTabs(qtbot)
    tabWidget.resize(600, 400)
    tabWidget.show()
    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)

    tabWidget.resize(840, 400)

    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)


def testThreeTabsShareThirds(qtbot) -> None:
    tabWidget = withTabs(qtbot, "One", "Two", "Three")
    tabWidget.resize(600, 400)
    tabWidget.show()

    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)


def testTheLabelsStandOutFromTheRestOfTheInterface(qtbot) -> None:
    tabWidget = withTabs(qtbot, "Beam", "Plate")

    font = tabWidget.tabBar().font()
    assert font.bold()
    assert font.pointSizeF() > QFont().pointSizeF()


def testTheOpenTabIsPaintedLikeThePageBelowIt(qtbot) -> None:
    """Tab and page share one surface; that is what says the page belongs to the tab."""
    tabWidget = withTabs(qtbot, "Beam", "Plate")
    style = tabWidget.styleSheet()

    openTab = rule(style, "QTabBar::tab:selected {")
    # Left to Qt to resolve while painting, so the tab cannot drift from its page.
    assert "background: palette(window)" in openTab
    assert "border-bottom: 1px solid palette(window)" in openTab  # it opens into the page
    page, _ink = tabStyling.pageAndInk(tabWidget)
    accent = tabTheme.accentFor(page)
    assert f"border-top: {fullWidthTabWidget.accentBar}px solid {accent}" in openTab
    assert "font-weight: bold" in openTab

    closedTab = rule(style, "> QTabBar::tab {")
    assert "background: palette(window)" not in closedTab  # a ground of its own
    assert "font-weight: normal" in closedTab
    assert "background: palette(window)" in rule(style, "::pane {")


def testTheStyleIsScopedToTheAppsTabControls(qtbot) -> None:
    """Every rule names the property these controls carry, so nothing else takes it."""
    tabWidget = withTabs(qtbot)
    style = tabWidget.styleSheet()

    assert tabWidget.property("highlightedTabs") is True
    rules = [part.split("{", 1)[0].strip() for part in style.split("}") if "{" in part]
    assert rules and all(selector.startswith(fullWidthTabWidget.scope) for selector in rules)


def testTheAccentBarIsPaintedOnTheOpenTabOnly(qtbot) -> None:
    tabWidget = withTabs(qtbot, "Beam", "Plate")
    tabWidget.resize(600, 400)
    tabWidget.show()
    qtbot.waitExposed(tabWidget)
    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)

    assert accentIsPaintedOn(tabWidget, 0)
    assert not accentIsPaintedOn(tabWidget, 1)

    tabWidget.setCurrentIndex(1)

    assert accentIsPaintedOn(tabWidget, 1)
    assert not accentIsPaintedOn(tabWidget, 0)


def testAChildControlIsMarkedExactlyLikeItsParent(qtbot) -> None:
    """The rule for the whole app: every tab control is highlighted, at any depth."""
    parent, child, _table = childControlInAPage()
    qtbot.addWidget(parent)

    assert child.property("highlightedTabs") is True
    assert child.styleSheet() == parent.styleSheet()
    assert child.tabBar().font() == parent.tabBar().font()


@pytest.mark.parametrize("childFirst", [False, True])
def testTheAccentBarIsPaintedAtEveryDepth(qtbot, childFirst: bool) -> None:
    """Two style sheets meet on the child's tab bar - its own and its parent's.

    Whichever Qt takes, the open tab of each control carries the accent and
    the closed ones do not.
    """
    parent, child, _table = childControlInAPage(childFirst)
    qtbot.addWidget(parent)
    parent.resize(700, 500)
    parent.show()
    qtbot.waitExposed(parent)
    qtbot.waitUntil(lambda: tabsFillHalves(parent) and tabsFillHalves(child), timeout=5000)

    for control in (parent, child):
        assert accentIsPaintedOn(control, 0)
        assert not accentIsPaintedOn(control, 1)

    child.setCurrentIndex(1)

    assert accentIsPaintedOn(child, 1)
    assert not accentIsPaintedOn(child, 0)
    assert accentIsPaintedOn(parent, 0)  # the parent's choice is untouched


def testTheDerivedTonesFollowTheApplicationsPalette(qtbot, qapp) -> None:
    """The closed tabs' ground is worked out here, so it has to follow a theme change.

    A colour no real theme uses, so this cannot pass on the palette the suite
    happens to run under. The palette is in place by the time the application
    says it changed - the colour scheme signal comes too early to read.
    """
    parent, child, _table = childControlInAPage()
    qtbot.addWidget(parent)
    original = qapp.palette()
    try:
        palette = QPalette(original)
        palette.setColor(QPalette.ColorRole.Window, QColor("#123456"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))

        qapp.setPalette(palette)  # as the system does when it switches theme
        qtbot.wait(20)

        ground = tabStyling.blend(
            QColor("#123456"), QColor("#ffffff"), tabStyling.closedGround
        ).name()
        for control in (parent, child):
            style = control.styleSheet()
            assert f"background: {ground}" in rule(style, "> QTabBar::tab {")
            # A dark page takes the lifted accent, which still reads against it.
            assert tabTheme.darkAccent in rule(style, "QTabBar::tab:selected {")
    finally:
        qapp.setPalette(original)


def testAnUnchangedPaletteDoesNotRebuildTheStyle(qtbot, monkeypatch) -> None:
    tabWidget = withTabs(qtbot)
    rebuilt: list[str] = []
    monkeypatch.setattr(tabWidget, "setStyleSheet", rebuilt.append)

    tabWidget.applyTheme()

    assert rebuilt == []


def testTheAccentReadsOnEitherPage() -> None:
    assert tabTheme.accentFor(QColor("#f3f3f3")) == tabTheme.lightAccent
    assert tabTheme.accentFor(QColor("#202020")) == tabTheme.darkAccent
    assert tabTheme.lightAccent != tabTheme.darkAccent


@pytest.mark.parametrize("childFirst", [False, True])
def testAThemeSwitchReachesWhatSitsUnderTheTabs(
    qtbot, qapp, observableColorScheme, childFirst: bool
) -> None:
    """The regression 26wagerBook met: with the tabs styled, Qt stopped handing
    palette changes to a nested tab widget, and Help > Theme > Light left the
    tables dark in a light window. Here the table sits under two levels of
    tabs. Only a real scheme change shows it, so this skips on the offscreen
    plugin and runs under a plain `pytest` on Windows."""
    if not observableColorScheme:
        pytest.skip("this platform plugin does not report a forced colour scheme")
    hints = qapp.styleHints()
    hints.setColorScheme(Qt.ColorScheme.Dark)
    parent, _child, table = childControlInAPage(childFirst)
    # Inside another widget, as the app's own controls are inside its window.
    holder = QWidget()
    qtbot.addWidget(holder)
    QVBoxLayout(holder).addWidget(parent)
    holder.show()
    qtbot.wait(200)

    for scheme in (Qt.ColorScheme.Light, Qt.ColorScheme.Dark, Qt.ColorScheme.Light):
        hints.setColorScheme(scheme)
        qtbot.waitUntil(
            lambda: table.palette().base().color() == qapp.palette().base().color(),
            timeout=3000,
        )


def testAThemeSwitchRestylesEveryLevelForTheNewPage(qtbot, qapp, observableColorScheme) -> None:
    """Help > Theme: the closed tabs' ground and the accent follow the new page."""
    if not observableColorScheme:
        pytest.skip("this platform plugin does not report a forced colour scheme")
    hints = qapp.styleHints()
    hints.setColorScheme(Qt.ColorScheme.Light)
    parent, child, _table = childControlInAPage()
    qtbot.addWidget(parent)
    parent.show()
    qtbot.wait(200)

    hints.setColorScheme(Qt.ColorScheme.Dark)

    qtbot.waitUntil(
        lambda: tabTheme.darkAccent in parent.styleSheet()
        and tabTheme.darkAccent in child.styleSheet(),
        timeout=3000,
    )
    qtbot.waitUntil(
        lambda: accentIsPaintedOn(parent, 0) and accentIsPaintedOn(child, 0), timeout=3000
    )


def testRestylingLeavesNoFixedPaletteBehind(qtbot) -> None:
    """A fixed palette would stop the next theme switch reaching what is under the tabs."""
    parent, child, _table = childControlInAPage()
    qtbot.addWidget(parent)

    for control in (parent, child):
        control.applyTheme()

        assert not control.testAttribute(Qt.WidgetAttribute.WA_SetPalette)

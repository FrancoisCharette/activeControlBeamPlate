"""Smoke tests for the main window."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeySequence, QStandardItemModel
from PySide6.QtWidgets import QTableView, QTabWidget

from activeControlBeamPlate import appConfig
from activeControlBeamPlate.services import themeService, windowStateService
from activeControlBeamPlate.ui import tabTheme
from activeControlBeamPlate.ui.mainWindow import MainWindow
from activeControlBeamPlate.ui.widgets.fullWidthTabWidget import FullWidthTabWidget
from activeControlBeamPlate.ui.widgets.reportingView import ReportingView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


def testMainWindowOpens(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    mainWindow.show()

    assert mainWindow.isVisible()
    assert mainWindow.windowTitle() == "Active Control Beam & Plate"
    assert mainWindow.statusBar().currentMessage() == "Ready"


def testTheWindowIsTheBeamAndPlateTabs(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    mainWindow.show()

    assert mainWindow.centralWidget() is mainWindow.structureTabs
    assert mainWindow.structureTabs.pageTitles() == ["Beam", "Plate"]
    assert mainWindow.structureTabs.tabs.isVisible()


def testClickingPlateOpensThePlatePage(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    mainWindow.show()
    qtbot.waitExposed(mainWindow)
    structureTabs = mainWindow.structureTabs
    tabBar = structureTabs.tabs.tabBar()

    qtbot.mouseClick(tabBar, Qt.MouseButton.LeftButton, pos=tabBar.tabRect(1).center())

    assert structureTabs.tabs.currentWidget() is structureTabs.plateView
    assert structureTabs.plateView.isVisible()
    assert not structureTabs.beamView.isVisible()


def testEveryTabControlInTheWindowIsHighlighted(qtbot) -> None:
    """The rule for the whole app: no bare QTabWidget, at any depth.

    Child controls are added here the way the app will grow, so the check
    covers levels the app does not have yet; it then holds for every view
    added later, because the window is searched rather than a list kept.
    """
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    configuration = TabbedView()
    configuration.addPage("Variant", TabbedView())
    mainWindow.structureTabs.beamView.addPage("Added Configuration", configuration)

    controls = mainWindow.findChildren(QTabWidget)

    assert len(controls) >= 4  # the switch, both structures, and the levels added above
    assert all(isinstance(control, FullWidthTabWidget) for control in controls)


def testAPageDeepInTheTabsReachesTheWindow(qtbot, monkeypatch) -> None:
    """Status to the bar and failures to a dialog, from a page nobody connected by hand."""
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    shown: list[tuple[str, str]] = []
    monkeypatch.setattr(
        MainWindow,
        "showError",
        lambda self, title, message: shown.append((title, message)),
    )
    configuration = TabbedView()
    page = ReportingView()
    configuration.addPage("Page", page)
    mainWindow.structureTabs.plateView.addPage("Added Configuration", configuration)

    page.reportStatus("Solving...")
    assert mainWindow.statusBar().currentMessage() == "Solving..."

    page.reportError("Model", "The model did not converge.\nRefine the mesh and run again.")

    assert shown == [("Model", "The model did not converge.\nRefine the mesh and run again.")]
    assert mainWindow.statusBar().currentMessage() == "The model did not converge."


def testHelpThemeRepaintsEveryLevelOfTabs(qtbot, qapp, observableColorScheme) -> None:
    """Help > Theme has to reach a page three tab controls down, not only the switch.

    Styled tabs stop passing palette changes on unless they are told to; see
    FullWidthTabWidget.reinheritPalette. Only a real scheme change shows it,
    so this skips on the offscreen plugin and runs under a plain `pytest`.
    """
    if not observableColorScheme:
        pytest.skip("this platform plugin does not report a forced colour scheme")
    qapp.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    table = QTableView()
    table.setModel(QStandardItemModel(2, 2))
    configuration = TabbedView()
    configuration.addPage("Table", table)
    mainWindow.structureTabs.beamView.addPage("Added Configuration", configuration)
    mainWindow.show()
    qtbot.wait(200)
    controls = mainWindow.findChildren(FullWidthTabWidget)
    accents = {
        themeService.lightTheme: tabTheme.lightAccent,
        themeService.darkTheme: tabTheme.darkAccent,
    }

    for theme in (themeService.lightTheme, themeService.darkTheme, themeService.lightTheme):
        mainWindow.themeActions[theme].trigger()

        qtbot.waitUntil(
            lambda: table.palette().base().color() == qapp.palette().base().color(),
            timeout=3000,
        )
        qtbot.waitUntil(
            lambda: all(accents[theme] in control.styleSheet() for control in controls),
            timeout=3000,
        )


def testMenuBarStructure(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    menuTitles = [action.text() for action in mainWindow.menuBar().actions()]
    assert menuTitles == ["&File", "&Help"]

    fileItems = [a.text() for a in mainWindow.fileMenu.actions() if not a.isSeparator()]
    assert fileItems == ["&New", "&Open...", "&Save", "E&xit"]
    assert any(a.isSeparator() for a in mainWindow.fileMenu.actions())

    helpItems = [a.text() for a in mainWindow.helpMenu.actions() if not a.isSeparator()]
    assert helpItems == ["&Theme", "User &Manual...", "&About"]


def testThemeMenuOffersSystemLightDark(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    labels = [a.text() for a in mainWindow.themeMenu.actions()]
    assert labels == ["Use &System Theme", "&Light", "&Dark"]
    assert all(a.isCheckable() for a in mainWindow.themeMenu.actions())
    assert mainWindow.themeGroup.isExclusive()
    # Following Windows is the default.
    assert mainWindow.themeActions[themeService.systemTheme].isChecked()


def testChoosingDarkAppliesAndRemembersIt(qtbot, observableColorScheme) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    mainWindow.themeActions[themeService.darkTheme].trigger()

    # The window's own job: remember the choice and say so.
    assert themeService.loadTheme() == themeService.darkTheme
    assert "Dark theme applied" in mainWindow.statusBar().currentMessage()
    # Whether Qt then paints dark is only observable on some platforms.
    if observableColorScheme:
        assert themeService.currentColorScheme() == Qt.ColorScheme.Dark


def testSavedThemeIsRestoredOnNextLaunch(qtbot) -> None:
    first = MainWindow()
    qtbot.addWidget(first)
    first.themeActions[themeService.lightTheme].trigger()

    reopened = MainWindow()
    qtbot.addWidget(reopened)

    assert reopened.themeActions[themeService.lightTheme].isChecked()


def testFileMenuPlaceholdersUpdateStatus(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    mainWindow.newAction.trigger()
    assert mainWindow.statusBar().currentMessage() == "File > New selected"

    mainWindow.openAction.trigger()
    assert mainWindow.statusBar().currentMessage() == "File > Open selected"

    mainWindow.saveAction.trigger()
    assert mainWindow.statusBar().currentMessage() == "File > Save selected"


def testAboutOpensTheDialogAndReportsADonation(qtbot, monkeypatch) -> None:
    """The About text itself is covered in testAboutDialog."""
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    monkeypatch.setattr(
        "activeControlBeamPlate.ui.mainWindow.showAbout", lambda parent: True
    )

    mainWindow.onHelpAbout()

    assert "donation page" in mainWindow.statusBar().currentMessage()


def openedUrls(monkeypatch) -> list[str]:
    """Collect what the app asked the desktop to open, and say it worked."""
    opened: list[str] = []
    monkeypatch.setattr(
        "activeControlBeamPlate.ui.mainWindow.QDesktopServices.openUrl",
        lambda url: opened.append(url.toString()) or True,
    )
    return opened


def testManualHasTheStandardHelpShortcut(qtbot) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    assert mainWindow.manualAction.shortcut() == QKeySequence.StandardKey.HelpContents


def testTheStubManualShipsWithTheTemplate() -> None:
    """Without it the menu item would fail the first time anybody clicked it."""
    assert appConfig.manualPath.exists()
    assert appConfig.manualPath.read_text(encoding="utf-8").strip()


def testNothingIsPublishedUntilTheAuthorSaysSo() -> None:
    """A new app has no manual online, so the default must not pretend it has."""
    assert appConfig.manualUrl == ""


def testTheLocalCopyIsOpenedWhenNothingIsPublished(qtbot, monkeypatch) -> None:
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    opened = openedUrls(monkeypatch)

    mainWindow.openManual(publishedIsReachable=False)

    assert len(opened) == 1
    assert opened[0].startswith("file:")
    assert opened[0].endswith("README.md")
    assert "local copy" in mainWindow.statusBar().currentMessage()


def testThePublishedCopyWinsWhenItAnswers(qtbot, monkeypatch) -> None:
    """Set manualUrl and the behaviour switches, with no other change."""
    monkeypatch.setattr(appConfig, "manualUrl", "https://example.invalid/manual")
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    opened = openedUrls(monkeypatch)

    mainWindow.openManual(publishedIsReachable=True)

    assert opened == ["https://example.invalid/manual"]
    assert "browser" in mainWindow.statusBar().currentMessage()


def testAMissingManualLeavesTheReaderAnAddress(qtbot, monkeypatch, tmp_path) -> None:
    """Nothing opened, so the path has to be readable somewhere."""
    monkeypatch.setattr(appConfig, "manualPath", tmp_path / "gone.md")
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    openedUrls(monkeypatch)
    shown: list[str] = []
    monkeypatch.setattr(
        "activeControlBeamPlate.ui.mainWindow.QMessageBox.information",
        lambda parent, title, text: shown.append(text),
    )

    mainWindow.openManual(publishedIsReachable=False)

    assert shown and "gone.md" in shown[0]
    assert "nothing published" in shown[0]


def testTheCheckRunsOffTheInterfaceThread(qtbot, monkeypatch) -> None:
    """A network probe can hang until its timeout; the window must not."""
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    openedUrls(monkeypatch)

    with qtbot.waitSignal(mainWindow.manualAction.changed, timeout=5000):
        mainWindow.onHelpManual()
    # Disabled while the probe is in flight, so it cannot be started twice.
    assert not mainWindow.manualAction.isEnabled()

    assert mainWindow.manualWorker is not None
    mainWindow.manualWorker.wait(5000)
    qtbot.waitUntil(lambda: mainWindow.manualWorker is None, timeout=5000)
    assert mainWindow.manualAction.isEnabled()


def testTheWindowSavesItsGeometryOnCloseAndRestoresItNextTime(qtbot, monkeypatch) -> None:
    """Placing it is Qt's job - restoreGeometry fits it to the screens there are - so
    this checks the hand-off."""
    first = MainWindow()
    qtbot.addWidget(first)
    first.show()
    first.close()
    saved = windowStateService.loadGeometry()
    assert saved is not None and not saved.isEmpty()
    restored: list = []
    monkeypatch.setattr(MainWindow, "restoreGeometry",
                        lambda self, state: restored.append(state) or True)

    second = MainWindow()
    qtbot.addWidget(second)

    assert restored == [saved]


def testTheFirstRunUsesTheDefaultSizeAndTabs(qtbot, monkeypatch) -> None:
    """Nothing saved yet, so nothing to restore: the configured size and the first tabs."""
    restored: list = []
    monkeypatch.setattr(MainWindow, "restoreGeometry",
                        lambda self, state: restored.append(state) or True)

    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)

    assert restored == []
    assert mainWindow.size().toTuple() == (
        appConfig.defaultWindowWidth, appConfig.defaultWindowHeight
    )
    assert mainWindow.structureTabs.openTabs() == {
        "": "Beam",
        "Beam": "Configuration", "Beam/Configuration": "Schematic",
        "Plate": "Configuration", "Plate/Configuration": "Schematic",
    }


def testTheOpenTabsAreSavedOnCloseAndReopenedNextTime(qtbot) -> None:
    first = MainWindow()
    qtbot.addWidget(first)
    first.show()
    structure = first.structureTabs
    structure.tabs.setCurrentWidget(structure.plateView)
    structure.plateView.tabs.setCurrentWidget(structure.plateView.sensingView)
    structure.beamView.tabs.setCurrentWidget(structure.beamView.actuationView)
    beamConfiguration = structure.beamView.configurationView
    beamConfiguration.tabs.setCurrentWidget(beamConfiguration.parametersView)
    first.close()

    second = MainWindow()
    qtbot.addWidget(second)

    reopened = second.structureTabs
    assert reopened.tabs.currentWidget() is reopened.plateView
    assert reopened.plateView.tabs.currentWidget() is reopened.plateView.sensingView
    assert reopened.beamView.tabs.currentWidget() is reopened.beamView.actuationView
    reopenedConfiguration = reopened.beamView.configurationView
    assert reopenedConfiguration.tabs.currentWidget() is reopenedConfiguration.parametersView
    plateConfiguration = reopened.plateView.configurationView
    assert plateConfiguration.tabs.currentWidget() is plateConfiguration.schematicView


def testAMovedWindowComesBackWhereItWas(qtbot, qapp) -> None:
    """The real round trip, on the real platform; offscreen has no desktop to place it on."""
    if qapp.platformName() == "offscreen":
        pytest.skip("the offscreen platform has no real screens to place a window on")
    first = MainWindow()
    qtbot.addWidget(first)
    first.show()
    qtbot.waitExposed(first)
    first.resize(700, 500)
    first.move(first.pos() + QPoint(40, 30))
    qtbot.wait(50)
    geometry = first.geometry()
    first.close()

    second = MainWindow()
    qtbot.addWidget(second)
    second.show()
    qtbot.waitExposed(second)

    assert second.geometry() == geometry

"""Tests for the Beam > Configuration > Schematic tab: Figure 2.1."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QImage, QPalette, QPixmap
from PySide6.QtWidgets import QLabel

from activeControlBeamPlate import appConfig
from activeControlBeamPlate.services import themeService
from activeControlBeamPlate.ui.beam.beamConfigurationView import BeamConfigurationView
from activeControlBeamPlate.ui.beam.beamSchematicView import BeamSchematicView
from activeControlBeamPlate.ui.mainWindow import MainWindow
from activeControlBeamPlate.ui.widgets.scaledImageView import ScaledImageView


def testTheFigureShipsWithTheApp() -> None:
    """Print resolution, so it stays sharp however large the window is made."""
    pixmap = QPixmap(str(appConfig.beamSchematicImage))

    assert not pixmap.isNull()
    assert pixmap.width() >= 3000
    # A wide drawing: the beam runs across it.
    assert 1.5 < pixmap.width() / pixmap.height() < 2.5


def testItShowsFigure21WithItsCaptionAndAKeyToTheFrenchLabels(qtbot) -> None:
    view = BeamSchematicView()
    qtbot.addWidget(view)

    assert isinstance(view.figure, ScaledImageView)
    assert view.captionLabel.text() == "Figure 2.1: Diagram of the system considered"
    for french, english in (("Actionneur", "actuator"), ("Poutre", "beam"), ("Capteur", "sensor")):
        assert f"{french}: {english}" in view.keyLabel.text()


def testItIsTheSchematicTabOfTheBeamConfiguration(qtbot) -> None:
    configuration = BeamConfigurationView()
    qtbot.addWidget(configuration)

    assert isinstance(configuration.schematicView, BeamSchematicView)
    assert configuration.tabs.widget(1) is configuration.schematicView


def testAMissingImageSaysWhereItShouldBe(qtbot, monkeypatch, tmp_path) -> None:
    """Shown in the page, with the path, rather than an empty page."""
    monkeypatch.setattr(appConfig, "beamSchematicImage", tmp_path / "gone.png")

    view = BeamSchematicView()
    qtbot.addWidget(view)

    assert isinstance(view.figure, QLabel)
    assert "gone.png" in view.figure.text()


def testTheFigureKeepsItsProportionsInAnyShapeOfPage(qtbot) -> None:
    view = BeamSchematicView()
    qtbot.addWidget(view)
    figure = view.figure
    ratio = figure.aspectRatio()

    for width, height in ((900, 300), (400, 900), (1200, 700)):
        figure.resize(width, height)
        rect = figure.imageRect()
        assert rect.width() <= width and rect.height() <= height
        assert rect.width() == width or rect.height() == height  # as large as fits
        assert abs(rect.height() / rect.width() - ratio) < 0.01
        assert rect.center() == figure.rect().center()


def testTheImageIsScaledOnceForEachSize(qtbot) -> None:
    """grab() paints whether or not the window is on screen, unlike repaint()."""
    view = BeamSchematicView()
    qtbot.addWidget(view)
    view.resize(800, 500)
    figure = view.figure
    figure.resize(700, 400)
    figure.grab()
    first = figure.scaled

    figure.grab()

    assert first is not None and figure.scaled is first

    figure.resize(500, 300)
    figure.grab()

    assert figure.scaled is not first


def aLinePoint() -> QPoint:
    """A pixel the figure draws black: the first one along its middle row."""
    source = QImage(str(appConfig.beamSchematicImage)).convertToFormat(
        QImage.Format.Format_Grayscale8
    )
    y = source.height() // 2
    x = next(x for x in range(source.width()) if source.pixelColor(x, y).value() < 40)
    return QPoint(x, y)


def inkOf(view: BeamSchematicView) -> QColor:
    return view.figure.palette().color(QPalette.ColorRole.WindowText)


def testTheFigureIsDrawnInTheTextColourOnNoBackgroundOfItsOwn(qtbot) -> None:
    """The bug: a white sheet in the dark theme. The paper is now see-through."""
    view = BeamSchematicView()
    qtbot.addWidget(view)
    image = view.figure.pixmap.toImage()

    assert image.pixelColor(0, 0).alpha() == 0  # the paper
    line = image.pixelColor(aLinePoint())
    assert line.alpha() > 230
    assert line.rgb() == inkOf(view).rgb()


def testAPaletteChangeRedrawsTheFigureInTheNewInk(qtbot) -> None:
    """A colour no real theme uses, so this cannot pass on the suite's own palette."""
    view = BeamSchematicView()
    qtbot.addWidget(view)
    palette = QPalette(view.figure.palette())
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#12ab34"))

    view.figure.setPalette(palette)

    line = view.figure.pixmap.toImage().pixelColor(aLinePoint())
    assert line.rgb() == QColor("#12ab34").rgb()
    assert view.figure.scaled is None  # the old size-matched copy is not reused


def testAnUnchangedInkIsNotRedrawn(qtbot) -> None:
    view = BeamSchematicView()
    qtbot.addWidget(view)
    before = view.figure.pixmap

    view.figure.applyPalette()

    assert view.figure.pixmap is before


def testHelpThemeReachesTheFigure(qtbot, qapp, observableColorScheme) -> None:
    """Three tab controls down, through styled tabs. Only a real scheme change shows
    it, so this skips on the offscreen plugin and runs under a plain `pytest`."""
    if not observableColorScheme:
        pytest.skip("this platform plugin does not report a forced colour scheme")
    mainWindow = MainWindow()
    qtbot.addWidget(mainWindow)
    mainWindow.show()
    view = mainWindow.structureTabs.beamView.configurationView.schematicView
    point = aLinePoint()

    def figureFollows(dark: bool) -> bool:
        """The lines are in the theme's text colour, and that colour reads on its page."""
        ink = qapp.palette().color(QPalette.ColorRole.WindowText)
        drawn = view.figure.pixmap.toImage().pixelColor(point)
        return drawn.rgb() == ink.rgb() and (ink.lightnessF() > 0.5) == dark

    for theme in (themeService.darkTheme, themeService.lightTheme, themeService.darkTheme):
        mainWindow.themeActions[theme].trigger()
        dark = theme == themeService.darkTheme
        qtbot.waitUntil(lambda: figureFollows(dark), timeout=3000)
    assert qapp.styleHints().colorScheme() == Qt.ColorScheme.Dark

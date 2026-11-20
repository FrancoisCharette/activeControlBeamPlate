"""Tests for the Plate > Configuration > Schematic tab: Figure 5.1."""

from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage, QPalette, QPixmap
from PySide6.QtWidgets import QLabel

from activeControlBeamPlate import appConfig
from activeControlBeamPlate.ui.plate.plateConfigurationView import PlateConfigurationView
from activeControlBeamPlate.ui.plate.plateSchematicView import PlateSchematicView
from activeControlBeamPlate.ui.widgets.figureView import FigureView
from activeControlBeamPlate.ui.widgets.scaledImageView import ScaledImageView


def testTheFigureShipsWithTheApp() -> None:
    """Print resolution, and a figure of its own rather than the beam's."""
    pixmap = QPixmap(str(appConfig.plateSchematicImage))

    assert not pixmap.isNull()
    assert pixmap.width() >= 3000
    # A wide drawing: the plate in plan and its section A-A side by side.
    assert 2.5 < pixmap.width() / pixmap.height() < 3.5
    assert appConfig.plateSchematicImage != appConfig.beamSchematicImage


def testItShowsFigure51WithItsCaptionAndAKeyToTheFrenchLabels(qtbot) -> None:
    view = PlateSchematicView()
    qtbot.addWidget(view)

    assert isinstance(view, FigureView)
    assert isinstance(view.figure, ScaledImageView)
    assert view.captionLabel.text() == (
        "Figure 5.1: Diagram of the plate-actuator configuration considered"
    )
    for french, english in (
        ("Plaque", "plate"),
        ("Actionneur", "actuator"),
        ("Conditions limites", "boundary conditions"),
        ("Coupe A-A", "section A-A"),
    ):
        assert f"{french}: {english}" in view.keyLabel.text()


def testItIsTheSchematicTabOfThePlateConfiguration(qtbot) -> None:
    configuration = PlateConfigurationView()
    qtbot.addWidget(configuration)

    assert isinstance(configuration.schematicView, PlateSchematicView)
    assert configuration.tabs.widget(1) is configuration.schematicView


def testItFollowsTheThemeLikeTheBeamFigure(qtbot) -> None:
    """Lines in the text colour, no paper of its own; a new palette re-inks it."""
    view = PlateSchematicView()
    qtbot.addWidget(view)
    source = QImage(str(appConfig.plateSchematicImage)).convertToFormat(
        QImage.Format.Format_Grayscale8
    )
    y = source.height() // 2
    lineX = next(x for x in range(source.width()) if source.pixelColor(x, y).value() < 40)
    point = QPoint(lineX, y)

    image = view.figure.pixmap.toImage()
    assert image.pixelColor(0, 0).alpha() == 0
    ink = view.figure.palette().color(QPalette.ColorRole.WindowText)
    assert image.pixelColor(point).rgb() == ink.rgb()

    palette = QPalette(view.figure.palette())
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#12ab34"))
    view.figure.setPalette(palette)

    assert view.figure.pixmap.toImage().pixelColor(point).rgb() == QColor("#12ab34").rgb()


def testAMissingImageSaysWhereItShouldBe(qtbot, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(appConfig, "plateSchematicImage", tmp_path / "gone.png")

    view = PlateSchematicView()
    qtbot.addWidget(view)

    assert isinstance(view.figure, QLabel)
    assert "gone.png" in view.figure.text()

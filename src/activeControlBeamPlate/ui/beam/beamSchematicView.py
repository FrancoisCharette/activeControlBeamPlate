"""The Schematic tab under Beam > Configuration: Figure 2.1 of the thesis.

The figure is the beam system as the thesis draws it - the beam, the
actuator above it, the sensor below it, the springs at its ends - with the
dimensions the Parameters tab asks for. It is shown as large as the page
allows, in the theme's text colour on the page's own colour, with its caption
and a key to its French labels underneath.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from activeControlBeamPlate import appConfig
from activeControlBeamPlate.ui.widgets.reportingView import ReportingView
from activeControlBeamPlate.ui.widgets.scaledImageView import ScaledImageView

logger = logging.getLogger(__name__)

caption = "Figure 2.1: Diagram of the system considered"
# The figure is the original drawing, so its labels are in French.
labelKey = "Actionneur: actuator  ·  Poutre: beam  ·  Capteur: sensor"


class BeamSchematicView(ReportingView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        pixmap = QPixmap(str(appConfig.beamSchematicImage))
        if pixmap.isNull():
            # Shown in place rather than in a dialog: nothing was asked for
            # yet, and the page has nothing else to show.
            logger.warning("Beam schematic not found at %s", appConfig.beamSchematicImage)
            self.figure: QWidget = QLabel(
                f"The schematic could not be loaded. It should be at:\n"
                f"{appConfig.beamSchematicImage}"
            )
            self.figure.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.figure.setWordWrap(True)
            self.figure.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        else:
            # Drawn in the theme's own ink on the page's colour, like the text.
            self.figure = ScaledImageView(pixmap, followsPalette=True)
            self.figure.setToolTip(labelKey)
        layout.addWidget(self.figure, 1)

        self.captionLabel = QLabel(caption)
        self.captionLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.keyLabel = QLabel(labelKey)
        self.keyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.keyLabel.setForegroundRole(QPalette.ColorRole.PlaceholderText)
        layout.addWidget(self.captionLabel)
        layout.addWidget(self.keyLabel)

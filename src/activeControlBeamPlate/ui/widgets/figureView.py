"""A page that shows one figure from the thesis, with its caption and a key to its labels.

The figure is shown as large as the page allows, drawn in the theme's text
colour on the page's own colour (the thesis figures are line art), with its
caption and, because the figures are the original drawings, a key to their
French labels underneath. A schematic tab inherits this and names its figure.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from activeControlBeamPlate.ui.widgets.reportingView import ReportingView
from activeControlBeamPlate.ui.widgets.scaledImageView import ScaledImageView

logger = logging.getLogger(__name__)


class FigureView(ReportingView):
    def __init__(
        self, imagePath: Path, caption: str, labelKey: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)

        pixmap = QPixmap(str(imagePath))
        if pixmap.isNull():
            # Shown in place rather than in a dialog: nothing was asked for
            # yet, and the page has nothing else to show.
            logger.warning("Figure not found at %s", imagePath)
            self.figure: QWidget = QLabel(
                f"The figure could not be loaded. It should be at:\n{imagePath}"
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
        self.captionLabel.setWordWrap(True)
        self.keyLabel = QLabel(labelKey)
        self.keyLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.keyLabel.setWordWrap(True)
        self.keyLabel.setForegroundRole(QPalette.ColorRole.PlaceholderText)
        layout.addWidget(self.captionLabel)
        layout.addWidget(self.keyLabel)

"""An image that fills the space it is given, keeping its proportions.

For figures from the thesis, which are stored at print resolution: the image
is scaled down smoothly to the widget's size, in device pixels, so it stays
sharp on a high-DPI screen and lines do not break up when it is made small.
The scaled copy is kept until the size changes, so repainting costs nothing.

Line art - black lines on white, as the thesis figures are - can follow the
app's theme (`followsPalette`): its darkness becomes the opacity of the
window's text colour, and its white becomes transparent, so the figure is
drawn in the same ink as the text around it, on the page's own colour, with
its anti-aliased edges intact. It is redone when the palette changes, which
is how Help > Theme reaches a widget.
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, QRect, QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPaintEvent, QPalette, QPixmap
from PySide6.QtWidgets import QSizePolicy, QWidget


def inkedLineArt(source: QPixmap, ink: QColor) -> QPixmap:
    """Line art redrawn in `ink`: dark becomes opaque ink, white becomes transparent."""
    coverage = source.toImage().convertToFormat(QImage.Format.Format_Grayscale8)
    coverage.invertPixels()  # black line -> 255, white paper -> 0
    inked = QImage(coverage.size(), QImage.Format.Format_ARGB32_Premultiplied)
    inked.fill(ink)
    inked.setAlphaChannel(coverage)
    return QPixmap.fromImage(inked)


class ScaledImageView(QWidget):
    def __init__(
        self, pixmap: QPixmap, followsPalette: bool = False, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.source = pixmap
        self.followsPalette = followsPalette
        self.pixmap = pixmap
        self.inkedWith: QColor | None = None
        self.scaled: QPixmap | None = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(160, 80)
        self.applyPalette()

    def ink(self) -> QColor:
        return self.palette().color(QPalette.ColorRole.WindowText)

    def applyPalette(self) -> None:
        """Redraw line art in the current text colour; nothing to do for a photograph."""
        if not self.followsPalette or self.source.isNull():
            return
        ink = self.ink()
        if ink == self.inkedWith:
            return
        self.inkedWith = ink
        self.pixmap = inkedLineArt(self.source, ink)
        self.scaled = None
        self.update()

    def changeEvent(self, event: QEvent) -> None:
        # The new palette is in place by the time this arrives, unlike the
        # colour-scheme signal, which comes while the old one still is.
        if event.type() == QEvent.Type.PaletteChange:
            self.applyPalette()
        super().changeEvent(event)

    def sizeHint(self) -> QSize:
        return QSize(640, round(640 * self.aspectRatio()))

    def aspectRatio(self) -> float:
        """Height over width."""
        if self.pixmap.isNull() or self.pixmap.width() == 0:
            return 0.5
        return self.pixmap.height() / self.pixmap.width()

    def imageRect(self) -> QRect:
        """Where the image is drawn: as large as fits, centred."""
        size = self.pixmap.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        rect = QRect(0, 0, size.width(), size.height())
        rect.moveCenter(self.rect().center())
        return rect

    def scaledPixmap(self, target: QRect) -> QPixmap:
        ratio = self.devicePixelRatioF()
        deviceSize = QSize(round(target.width() * ratio), round(target.height() * ratio))
        if self.scaled is None or self.scaled.size() != deviceSize:
            self.scaled = self.pixmap.scaled(
                deviceSize,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.scaled.setDevicePixelRatio(ratio)
        return self.scaled

    def paintEvent(self, event: QPaintEvent) -> None:
        if self.pixmap.isNull():
            return
        target = self.imageRect()
        if target.isEmpty():
            return
        painter = QPainter(self)
        painter.drawPixmap(target.topLeft(), self.scaledPixmap(target))

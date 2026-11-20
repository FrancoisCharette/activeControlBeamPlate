"""Draw Active Control Beam & Plate's application icon, the way 26wagerBook draws its own.

The icon is drawn with QPainter *at each size* rather than scaled down from
one large rendering, because a 16 px icon shrunk from 256 px is mush - its
strokes fall below a pixel and the shape stops reading. Each size thickens
its strokes and drops detail as it shrinks.

The artwork is the thesis in one picture: a beam bent in its first mode, on
two supports, with an amber piezoceramic actuator bonded at its middle - and
behind it, faint, the much larger bending of the same beam before control.
The bright beam is the vibration the actuator has cut down to. On a deep
blue-teal tile, so it is not taken for one of the group's indigo apps.

    python tools/makeIcons.py

Writes ``src/activeControlBeamPlate/resources/activeControlBeamPlate.ico``
(16 to 256 px) and a 1024 px PNG of the same drawing. The app finds them
through ``appConfig``, never by path.
"""

from __future__ import annotations

import math
import os
import struct
import sys
from pathlib import Path

# Before any QApplication exists: draw on the real platform, not offscreen.
os.environ.pop("QT_QPA_PLATFORM", None)

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo / "src"))
outputDir = repo / "src" / "activeControlBeamPlate" / "resources"
stem = "activeControlBeamPlate"

from PySide6.QtCore import QBuffer, QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import QApplication  # noqa: E402

# What a .ico carries: 16 is the title bar and taskbar, 256 the extra-large
# view in Explorer; the sizes between are what Windows picks at other DPIs.
iconSizes = (16, 24, 32, 48, 64, 128, 256)

tileTop = QColor("#1F7A99")
tileBottom = QColor("#0B3550")
beamColour = QColor("#FFFFFF")
envelopeColour = QColor(255, 255, 255, 95)  # the bending before control
actuatorColour = QColor("#FFB020")  # piezoceramic amber
actuatorEdge = QColor("#B86E00")
supportColour = QColor("#9ED9EC")


def roundPen(colour: QColor, width: float) -> QPen:
    pen = QPen(QBrush(colour), width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def beamEnds(size: int) -> tuple[float, float]:
    """Where the beam starts and ends across the tile; wider when small."""
    margin = 0.13 if size < 32 else 0.17
    return size * margin, size * (1 - margin)


def beamLevel(size: int) -> float:
    """The height of the supports - the beam's ends - on the tile."""
    return size * (0.56 if size >= 48 else 0.55)


def modeShape(size: int, amplitude: float, samples: int = 48) -> QPainterPath:
    """The first bending mode, a half sine between the supports, bulging upward."""
    left, right = beamEnds(size)
    level = beamLevel(size)
    path = QPainterPath()
    for index in range(samples + 1):
        fraction = index / samples
        point = QPointF(left + fraction * (right - left),
                        level - amplitude * math.sin(math.pi * fraction))
        if index == 0:
            path.moveTo(point)
        else:
            path.lineTo(point)
    return path


def drawTile(painter: QPainter, size: int) -> None:
    # Tighter corners when small, or the rounding eats the artwork.
    radius = size * (0.18 if size < 32 else 0.22)
    tile = QLinearGradient(QPointF(0, 0), QPointF(0, size))
    tile.setColorAt(0.0, tileTop)
    tile.setColorAt(1.0, tileBottom)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(tile)
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)


def drawEnvelope(painter: QPainter, size: int) -> None:
    """The vibration before control: the same mode, much larger, either way."""
    if size < 32:
        return  # at 16 and 24 px it would only blur the beam
    amplitude = size * 0.26
    width = max(1.2, size * 0.026)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(roundPen(envelopeColour, width))
    painter.drawPath(modeShape(size, amplitude))
    painter.drawPath(modeShape(size, -amplitude))


def drawSupports(painter: QPainter, size: int) -> None:
    """A triangle under each end, as Figure 2.1's pinned ends; dropped when small."""
    if size < 48:
        return
    left, right = beamEnds(size)
    level = beamLevel(size)
    half, height = size * 0.06, size * 0.1
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(supportColour)
    gap = size * 0.02  # under the beam's stroke, not into it
    for x in (left, right):
        painter.drawPolygon(QPolygonF([
            QPointF(x, level + gap),
            QPointF(x - half, level + gap + height),
            QPointF(x + half, level + gap + height),
        ]))


def drawBeam(painter: QPainter, size: int) -> None:
    """The controlled beam: the same mode, small, and bright."""
    amplitude = size * (0.12 if size < 32 else 0.08)
    width = max(2.0, size * (0.12 if size < 32 else 0.07))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.setPen(roundPen(beamColour, width))
    painter.drawPath(modeShape(size, amplitude))


def drawActuator(painter: QPainter, size: int) -> None:
    """The piezoceramic patch on top of the beam at its middle, where the mode peaks."""
    amplitude = size * (0.12 if size < 32 else 0.08)
    beamWidth = max(2.0, size * (0.12 if size < 32 else 0.07))
    length = size * (0.36 if size < 32 else 0.3)
    thickness = max(2.0, size * (0.13 if size < 32 else 0.085))
    top = beamLevel(size) - amplitude - beamWidth / 2 - thickness
    patch = QRectF(size / 2 - length / 2, top + size * 0.004, length, thickness)
    corner = thickness * 0.25
    if size >= 48:
        painter.setPen(QPen(actuatorEdge, max(1.0, size * 0.012)))
    else:
        painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(actuatorColour)
    painter.drawRoundedRect(patch, corner, corner)


def render(size: int) -> QPixmap:
    """The icon at one size, drawn rather than scaled."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    drawTile(painter, size)
    drawEnvelope(painter, size)
    drawSupports(painter, size)
    drawBeam(painter, size)
    drawActuator(painter, size)
    painter.end()
    return pixmap


def pngBytes(pixmap: QPixmap) -> bytes:
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    return bytes(buffer.data())


def packIco(images: list[tuple[int, bytes]]) -> bytes:
    """A multi-size .ico holding PNG entries.

    Written by hand rather than through Qt's writer, so every size is the one
    drawn at that size. Windows since Vista reads PNG inside an ICO, which
    keeps the 256 px entry small.
    """
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, payload = [], []
    for size, data in images:
        side = 0 if size >= 256 else size  # 0 means 256 in an ICO
        entries.append(struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(data), offset))
        payload.append(data)
        offset += len(data)
    return header + b"".join(entries) + b"".join(payload)


def main() -> int:
    application = QApplication.instance() or QApplication([])  # noqa: F841 - kept alive
    outputDir.mkdir(parents=True, exist_ok=True)
    ico = outputDir / f"{stem}.ico"
    ico.write_bytes(packIco([(size, pngBytes(render(size))) for size in iconSizes]))
    png = outputDir / f"{stem}.png"
    render(1024).save(str(png), "PNG")
    sizes = "/".join(str(size) for size in iconSizes)
    print(f"{ico.relative_to(repo)}  {ico.stat().st_size / 1024:.1f} kB  ({sizes} px)")
    print(f"{png.relative_to(repo)}  1024 px")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Tests for the application icon."""

from __future__ import annotations

import importlib.util
import struct

from PySide6.QtCore import QSize
from PySide6.QtGui import QIcon, QImage

from activeControlBeamPlate import appConfig
from activeControlBeamPlate.main import setAppIdentity

pngSignature = b"\x89PNG\r\n\x1a\n"


def iconEntries() -> list[tuple[int, bytes]]:
    """Each image in the .ico: its size and its bytes."""
    data = appConfig.iconFile.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", data, 0)
    assert (reserved, kind) == (0, 1)  # an icon, not a cursor
    entries = []
    for index in range(count):
        width, height, _, _, _, _, length, offset = struct.unpack_from(
            "<BBBBHHII", data, 6 + 16 * index
        )
        assert width == height
        assert offset + length <= len(data)
        entries.append((width or 256, data[offset:offset + length]))  # 0 means 256
    return entries


def testTheIconShipsWithEveryWindowsSize() -> None:
    entries = iconEntries()

    assert [size for size, _data in entries] == [16, 24, 32, 48, 64, 128, 256]
    assert all(data[:8] == pngSignature for _size, data in entries)


def testEachSizeIsDrawnRatherThanScaled(qapp) -> None:
    """The script draws every size itself; the file must be what it draws now.

    Fails if the drawing in tools/makeIcons.py was changed and the icon was
    not regenerated - run `python tools/makeIcons.py`.
    """
    spec = importlib.util.spec_from_file_location(
        "makeIcons", appConfig.projectRoot / "tools" / "makeIcons.py"
    )
    makeIcons = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(makeIcons)

    for size, data in iconEntries():
        shipped = QImage.fromData(data).convertToFormat(QImage.Format.Format_ARGB32)
        drawn = makeIcons.render(size).toImage().convertToFormat(QImage.Format.Format_ARGB32)
        assert shipped.size() == QSize(size, size)
        assert shipped == drawn, f"the {size} px icon is not what makeIcons draws now"


def testTheAppWearsTheIcon(qapp) -> None:
    try:
        setAppIdentity(qapp)

        icon = qapp.windowIcon()
        assert not icon.isNull()
        assert {QSize(16, 16), QSize(256, 256)} <= set(icon.availableSizes())
    finally:
        qapp.setWindowIcon(QIcon())


def testAMissingIconIsNotAFailure(qapp, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(appConfig, "iconFile", tmp_path / "missing.ico")
    qapp.setWindowIcon(QIcon())

    setAppIdentity(qapp)

    assert qapp.windowIcon().isNull()


def testTheTaskbarIdIsTheAppsOwn() -> None:
    """Not Python's, and not another Charette AI Group app's."""
    assert appConfig.appUserModelId == "Charette-AI-Group.ActiveControlBeamPlate"

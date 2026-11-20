"""Tests for what the window remembers between sessions."""

from __future__ import annotations

from PySide6.QtCore import QByteArray

from activeControlBeamPlate.services import settingsService, windowStateService


def testNothingIsRememberedOnTheFirstRun() -> None:
    assert windowStateService.loadGeometry() is None
    assert windowStateService.loadOpenTabs() == {}


def testTheGeometryComesBackAsSaved() -> None:
    blob = QByteArray(b"\x01\xd9\xd0\xcb geometry")

    windowStateService.saveGeometry(blob)

    assert windowStateService.loadGeometry() == blob


def testTheOpenTabsComeBackAsSaved() -> None:
    """Including the switch's own place, the empty string, and nested places with "/"."""
    openTabs = {"": "Plate", "Beam": "Actuation", "Plate": "Sensing", "Beam/Actuation": "Two"}

    windowStateService.saveOpenTabs(openTabs)

    assert windowStateService.loadOpenTabs() == openTabs


def testAnUnreadableSavedValueMeansTheFirstRunTabs() -> None:
    """A hand-edited or damaged settings file must not stop the app opening."""
    for damaged in ("{not json", "[1, 2]", '"Plate"'):
        settingsService.writeValue(windowStateService.openTabsKey, damaged)

        assert windowStateService.loadOpenTabs() == {}


def testEntriesThatAreNotTitlesAreDropped() -> None:
    settingsService.writeValue(
        windowStateService.openTabsKey, '{"": "Plate", "Beam": 3, "Plate": null}'
    )

    assert windowStateService.loadOpenTabs() == {"": "Plate"}


def testAPlaceIsTheTitlesAboveItJoined() -> None:
    assert windowStateService.tabPath("", "Beam") == "Beam"
    assert windowStateService.tabPath("Beam", "Actuation") == "Beam/Actuation"

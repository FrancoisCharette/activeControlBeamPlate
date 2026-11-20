"""Shared access to the app's INI settings file."""

from __future__ import annotations

from PySide6.QtCore import QSettings

from activeControlBeamPlate import appConfig


def openSettings() -> QSettings:
    return QSettings(str(appConfig.settingsFile), QSettings.Format.IniFormat)


def writeValue(key: str, value: object) -> None:
    writeValues({key: value})


def writeValues(values: dict[str, object]) -> None:
    """Several keys in one write of the file, rather than one write each."""
    appConfig.settingsFile.parent.mkdir(parents=True, exist_ok=True)
    settings = openSettings()
    for key, value in values.items():
        settings.setValue(key, value)
    settings.sync()

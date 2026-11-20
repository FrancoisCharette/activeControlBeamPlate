"""Where the window was and what it showed, restored at the next start.

Two things are kept in the settings file, both written when the window closes:

- The window's size and position, as Qt's own geometry blob. Restoring it
  checks the saved position against the screens that exist now, so a window
  last used on a monitor that is no longer attached comes back on screen
  instead of somewhere invisible. Maximised is part of the blob too.
- Which tab is open in every tab control, as a map from a control's place in
  the tree to the title of its open tab. A place is the titles of the tabs
  above it joined with "/" - "" for the Beam / Plate switch, "Beam" for the
  tabs under Beam - so each structure remembers its own sub-tab. Titles
  rather than positions, so a tab added or reordered later never opens the
  wrong page: a title that no longer exists is simply not restored.
"""

from __future__ import annotations

import json
import logging

from PySide6.QtCore import QByteArray

from activeControlBeamPlate.services import settingsService

logger = logging.getLogger(__name__)

geometryKey = "window/geometry"
openTabsKey = "window/openTabs"
# Joins the titles on the way down to a tab control into its place in the tree.
pathSeparator = "/"


def tabPath(parentPath: str, title: str) -> str:
    """The place of the tab control that sits in tab `title` of the control at `parentPath`."""
    return f"{parentPath}{pathSeparator}{title}" if parentPath else title


def loadGeometry() -> QByteArray | None:
    value = settingsService.openSettings().value(geometryKey)
    return value if isinstance(value, QByteArray) and not value.isEmpty() else None


def saveGeometry(state: QByteArray) -> None:
    settingsService.writeValue(geometryKey, state)


def loadOpenTabs() -> dict[str, str]:
    """The saved open tabs; empty on the first run or when the saved value is unreadable.

    An unreadable value costs the reader nothing worse than the first-run
    tabs, so it is logged rather than reported.
    """
    text = settingsService.openSettings().value(openTabsKey)
    if not text:
        return {}
    try:
        value = json.loads(str(text))
    except json.JSONDecodeError:
        logger.warning("Ignoring unreadable saved tabs: %r", text)
        return {}
    if not isinstance(value, dict):
        logger.warning("Ignoring saved tabs that are not a map: %r", value)
        return {}
    return {path: title for path, title in value.items()
            if isinstance(path, str) and isinstance(title, str)}


def saveOpenTabs(openTabs: dict[str, str]) -> None:
    # One JSON value rather than a key per control: QSettings reads "/" in a
    # key as a group, and the switch's own place is the empty string.
    settingsService.writeValue(openTabsKey, json.dumps(openTabs, sort_keys=True))

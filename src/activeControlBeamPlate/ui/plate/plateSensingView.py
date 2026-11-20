"""The Sensing tab under Plate.

How the plate's response is measured: the sensors and where they sit.

Its content - fields, or child tabs of its own - goes in __init__; for child
tabs, addPage each one, as README.md describes. None has been added yet, so
the page says so instead of showing an empty tab control.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class PlateSensingView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            emptyText="No plate sensing has been added yet.", parent=parent
        )

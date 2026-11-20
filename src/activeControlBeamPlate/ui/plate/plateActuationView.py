"""The Actuation tab under Plate.

How the plate is driven: the actuators, where they sit, and what drives
them.

Its content - fields, or child tabs of its own - goes in __init__; for child
tabs, addPage each one, as README.md describes. None has been added yet, so
the page says so instead of showing an empty tab control.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class PlateActuationView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            emptyText="No plate actuation has been added yet.", parent=parent
        )

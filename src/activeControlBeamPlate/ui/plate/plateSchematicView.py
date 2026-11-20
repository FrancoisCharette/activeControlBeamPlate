"""The Schematic tab under Plate > Configuration.

A drawing of the plate: its shape, supports, and where actuators and
sensors sit.

Its content - a drawing, fields, or child tabs of its own - goes in
__init__. None has been added yet, so the page says so.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class PlateSchematicView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            emptyText="No plate schematic has been added yet.", parent=parent
        )

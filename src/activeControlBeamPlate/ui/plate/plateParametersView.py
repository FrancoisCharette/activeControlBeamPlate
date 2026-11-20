"""The Parameters tab under Plate > Configuration.

The plate's parameters: geometry, material and boundary conditions.

Its content - a drawing, fields, or child tabs of its own - goes in
__init__. None has been added yet, so the page says so.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class PlateParametersView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            emptyText="No plate parameters have been added yet.", parent=parent
        )

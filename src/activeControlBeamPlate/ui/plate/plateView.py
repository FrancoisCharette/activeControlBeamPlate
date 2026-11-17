"""The Plate tab.

Each plate configuration becomes a child tab here, added in __init__ with
addPage; README.md has the steps. None has been added yet, so the page says
so instead of showing an empty tab control.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class PlateView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            emptyText="No plate configuration has been added yet.", parent=parent
        )

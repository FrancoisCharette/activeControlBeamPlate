"""The Configuration tab under Plate: the plate itself, in two tabs.

Parameters, first because it is where the work is, holds its geometry, materials
and boundary conditions; Schematic, the thesis's figure of it, is there to
look up what a symbol means. Each is a view of its own in this folder.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.plate.plateParametersView import PlateParametersView
from activeControlBeamPlate.ui.plate.plateSchematicView import PlateSchematicView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class PlateConfigurationView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.parametersView = PlateParametersView()
        self.schematicView = PlateSchematicView()
        self.addPage("Parameters", self.parametersView)
        self.addPage("Schematic", self.schematicView)

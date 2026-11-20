"""The Configuration tab under Plate: the plate itself, in two tabs.

Schematic shows the plate; Parameters holds its geometry, material and boundary
conditions. Each is a view of its own in this folder.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.plate.plateParametersView import PlateParametersView
from activeControlBeamPlate.ui.plate.plateSchematicView import PlateSchematicView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class PlateConfigurationView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.schematicView = PlateSchematicView()
        self.parametersView = PlateParametersView()
        self.addPage("Schematic", self.schematicView)
        self.addPage("Parameters", self.parametersView)

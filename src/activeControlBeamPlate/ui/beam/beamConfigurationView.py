"""The Configuration tab under Beam: the beam itself, in two tabs.

Schematic shows the beam; Parameters holds its geometry, material and boundary
conditions. Each is a view of its own in this folder.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.beam.beamParametersView import BeamParametersView
from activeControlBeamPlate.ui.beam.beamSchematicView import BeamSchematicView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class BeamConfigurationView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.schematicView = BeamSchematicView()
        self.parametersView = BeamParametersView()
        self.addPage("Schematic", self.schematicView)
        self.addPage("Parameters", self.parametersView)

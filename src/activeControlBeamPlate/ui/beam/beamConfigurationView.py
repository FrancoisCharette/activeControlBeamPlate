"""The Configuration tab under Beam: the beam itself, in two tabs.

Parameters, first because it is where the work is, holds its geometry, materials
and boundary conditions; Schematic, the thesis's figure of it, is there to
look up what a symbol means. Each is a view of its own in this folder.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.beam.beamParametersView import BeamParametersView
from activeControlBeamPlate.ui.beam.beamSchematicView import BeamSchematicView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class BeamConfigurationView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.parametersView = BeamParametersView()
        self.schematicView = BeamSchematicView()
        self.addPage("Parameters", self.parametersView)
        self.addPage("Schematic", self.schematicView)

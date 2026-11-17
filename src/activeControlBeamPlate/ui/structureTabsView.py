"""The window's top-level switch: is the structure a beam or a plate.

The most basic parameter of the thesis, so it is chosen first and everything
else sits under one of its two tabs. Each tab is a view of its own - ui/beam
and ui/plate - that takes child tabs as its configurations are added.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.beam.beamView import BeamView
from activeControlBeamPlate.ui.plate.plateView import PlateView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class StructureTabsView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        # The window's own switch runs edge to edge; only the controls inside
        # a page are set in from it.
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.beamView = BeamView()
        self.plateView = PlateView()
        self.addPage("Beam", self.beamView)
        self.addPage("Plate", self.plateView)

"""The Plate tab: a second-level tab control with the three parts of a plate study.

Configuration describes the plate itself, in a Parameters tab and a Schematic
tab; Actuation is how it is driven, and Sensing how its response is
measured. Each is a view of its own in this folder.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.plate.plateActuationView import PlateActuationView
from activeControlBeamPlate.ui.plate.plateConfigurationView import PlateConfigurationView
from activeControlBeamPlate.ui.plate.plateSensingView import PlateSensingView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class PlateView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.configurationView = PlateConfigurationView()
        self.actuationView = PlateActuationView()
        self.sensingView = PlateSensingView()
        self.addPage("Configuration", self.configurationView)
        self.addPage("Actuation", self.actuationView)
        self.addPage("Sensing", self.sensingView)

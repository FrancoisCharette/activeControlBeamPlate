"""The Beam tab: a second-level tab control with the three parts of a beam study.

Configuration describes the beam itself, in a Parameters tab and a Schematic
tab; Actuation is how it is driven, and Sensing how its response is
measured. Each is a view of its own in this folder.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate.ui.beam.beamActuationView import BeamActuationView
from activeControlBeamPlate.ui.beam.beamConfigurationView import BeamConfigurationView
from activeControlBeamPlate.ui.beam.beamSensingView import BeamSensingView
from activeControlBeamPlate.ui.widgets.tabbedView import TabbedView


class BeamView(TabbedView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.configurationView = BeamConfigurationView()
        self.actuationView = BeamActuationView()
        self.sensingView = BeamSensingView()
        self.addPage("Configuration", self.configurationView)
        self.addPage("Actuation", self.actuationView)
        self.addPage("Sensing", self.sensingView)

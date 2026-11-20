"""The Schematic tab under Beam > Configuration: Figure 2.1 of the thesis.

The figure is the beam system as the thesis draws it - the beam, the
actuator above it, the sensor below it, the springs at its ends - with the
dimensions the Parameters tab asks for. How it is shown is in FigureView.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate import appConfig
from activeControlBeamPlate.ui.widgets.figureView import FigureView

caption = "Figure 2.1: Diagram of the system considered"
# The figure is the original drawing, so its labels are in French.
labelKey = "Actionneur: actuator  ·  Poutre: beam  ·  Capteur: sensor"


class BeamSchematicView(FigureView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(appConfig.beamSchematicImage, caption, labelKey, parent)

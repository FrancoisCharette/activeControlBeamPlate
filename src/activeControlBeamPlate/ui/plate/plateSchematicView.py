"""The Schematic tab under Plate > Configuration: Figure 5.1 of the thesis.

The figure is the plate system of chapter 5 - a rectangular plate held at its
edges by distributed springs, with one actuator at (X_a, Y_a) - in plan and
in section A-A, where the actuator shows as a pair of piezoceramics, one on
each face. It has no sensor: the thesis adds the plate's PVDF sensors later,
and so will this app. How the figure is shown is in FigureView.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from activeControlBeamPlate import appConfig
from activeControlBeamPlate.ui.widgets.figureView import FigureView

caption = "Figure 5.1: Diagram of the plate-actuator configuration considered"
# The figure is the original drawing, so its labels are in French.
labelKey = (
    "Plaque: plate  ·  Actionneur: actuator  ·  Conditions limites: boundary conditions"
    "  ·  Coupe A-A: section A-A"
)


class PlateSchematicView(FigureView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(appConfig.plateSchematicImage, caption, labelKey, parent)

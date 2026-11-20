"""The Edge Supports group of Plate > Configuration > Parameters.

The distributed line springs of Figure 5.1, one row per edge of the plate,
each a transverse and a rotational stiffness per metre of edge, typed as its
real part and its imaginary part (the damping). The group only shows and
reads the values; the Parameters view keeps them.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QWidget

from activeControlBeamPlate.services.flatValues import join
from activeControlBeamPlate.ui.widgets.scientificSpinBox import ScientificSpinBox

edgesNote = (
    "Springs spread along the whole edge, per metre of edge: transverse resists the edge "
    "moving out of the plane, rotational resists it turning. Each is its real part + j × its "
    "imaginary part, the damping; 0 leaves the edge free that way, a very large value holds "
    "it. Table 5.1's plate is simply supported - held transversely, free to rotate - but the "
    "thesis does not give the stiffness values, so they start at 0."
)
edges = (
    ("edgeXNegative", "Edge x = -L<sub>x</sub>/2"),
    ("edgeXPositive", "Edge x = +L<sub>x</sub>/2"),
    ("edgeYNegative", "Edge y = -L<sub>y</sub>/2"),
    ("edgeYPositive", "Edge y = +L<sub>y</sub>/2"),
)
springs = (("transverse", "Transverse (N/m²)"), ("rotational", "Rotational (N/rad)"))


def richLabel(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.RichText)
    return label


class PlateEdgesBox(QGroupBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Edge Supports", parent)
        # By path under PlateConfiguration.supports, e.g. "edgeXNegative/transverse/real".
        self.inputs: dict[str, ScientificSpinBox] = {}
        grid = QGridLayout(self)
        grid.setColumnStretch(7, 1)
        for index, (_kind, title) in enumerate(springs):
            grid.addWidget(QLabel(title), 0, 1 + 3 * index, 1, 3, Qt.AlignmentFlag.AlignCenter)
        for row, (edge, title) in enumerate(edges, start=1):
            grid.addWidget(richLabel(title), row, 0)
            for index, (kind, _title) in enumerate(springs):
                self.addStiffness(grid, row, 1 + 3 * index, join(edge, kind))
        note = QLabel(edgesNote)
        note.setWordWrap(True)
        grid.addWidget(note, len(edges) + 1, 0, 1, 8)

    def addStiffness(self, grid: QGridLayout, row: int, column: int, path: str) -> None:
        for offset, part in ((0, "real"), (2, "imag")):
            spinBox = ScientificSpinBox()
            spinBox.setObjectName(path.replace("/", "_") + f"_{part}Input")
            spinBox.setMinimumWidth(100)
            spinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            spinBox.setKeyboardTracking(False)
            grid.addWidget(spinBox, row, column + offset)
            self.inputs[join(path, part)] = spinBox
        grid.addWidget(QLabel("+ j"), row, column + 1, Qt.AlignmentFlag.AlignCenter)

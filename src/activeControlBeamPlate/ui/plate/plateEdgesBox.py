"""The Edge Supports group of Plate > Configuration > Parameters.

The distributed line springs of Figure 5.1, laid out like the beam's End
Supports: for each edge, a heading with two buttons, then its transverse and
rotational spring, each typed as its real part and its imaginary part (the
damping), per metre of edge.

Condition, above the real parts, fills them with this app's recommended
stiffnesses for Free, Simply Supported or Clamped; Damping, above the
imaginary parts, sets them to a loss factor times the real parts. Both are
worked out in plateEdgeConditions. All Edges, at the top, does either for the
four edges at once. Each button says what the values are now - Custom once
they are not exactly what it put there, Mixed on All Edges when the edges
differ. Which condition fits needs the plate, which this group does not
have, so the Parameters view hands it `recognizeCondition`.

The group only shows and reads the values, and says which button was used;
the Parameters view keeps them.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QMenu, QPushButton, QWidget

from activeControlBeamPlate.models.plateConfiguration import PlateSupports
from activeControlBeamPlate.services.flatValues import join, rebuild
from activeControlBeamPlate.services.plateEdgeConditions import (
    EdgeCondition,
    conditionHelp,
    holdingFactor,
    lossFactorOf,
)
from activeControlBeamPlate.services.springDamping import (
    lossFactors,
    lossFactorText,
    offeredLevel,
)
from activeControlBeamPlate.ui.widgets.scientificSpinBox import ScientificSpinBox

allEdges = "all"
edgesNote = (
    "Springs spread along the whole edge, per metre of edge: transverse resists the edge "
    "moving out of the plane, rotational resists it turning. Each is its real part + j × its "
    "imaginary part, the damping; 0 leaves the edge free that way. Condition makes a held "
    f"spring {holdingFactor:,.0f} times the plate's own stiffness across that edge (D/L³, "
    "D/L, with D = E h³ / 12(1 - ν²)) - this app's recommendation; the thesis gives no values. "
    "Damping sets each imaginary part to the loss factor η × its real part. Table 5.1's plate "
    "is simply supported on all four edges."
)
conditionTip = "Fill the real parts with typical stiffnesses for a support"
dampingTip = (
    "Fill the imaginary parts with a loss factor η: imaginary = η × real, as the thesis "
    "writes damping"
)
edges = (
    ("edgeXNegative", "Edge x = -L<sub>x</sub>/2"),
    ("edgeXPositive", "Edge x = +L<sub>x</sub>/2"),
    ("edgeYNegative", "Edge y = -L<sub>y</sub>/2"),
    ("edgeYPositive", "Edge y = +L<sub>y</sub>/2"),
)
springs = (("transverse", "Transverse", "N/m²"), ("rotational", "Rotational", "N/rad"))


def richLabel(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.RichText)
    return label


class PlateEdgesBox(QGroupBox):
    # A Condition was picked: (edge field, or "all", EdgeCondition).
    conditionChosen = Signal(str, object)
    # A Damping was picked: (edge field, or "all", loss factor).
    lossFactorChosen = Signal(str, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Edge Supports", parent)
        # By path under PlateConfiguration.supports, e.g. "edgeXNegative/transverse/real".
        self.inputs: dict[str, ScientificSpinBox] = {}
        self.conditionButtons: dict[str, QPushButton] = {}
        self.dampingButtons: dict[str, QPushButton] = {}
        # Which condition an edge's springs are, given the plate; set by the view
        # that knows the plate. Until then nothing is recognised.
        self.recognizeCondition: Callable[[PlateSupports, str], EdgeCondition | None] = (
            lambda _supports, _edge: None
        )
        grid = QGridLayout(self)
        grid.setColumnStretch(5, 1)
        grid.addWidget(QLabel("Real Part"), 0, 1, Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel("Imaginary Part"), 0, 3, Qt.AlignmentFlag.AlignCenter)
        row = 1
        self.addHeading(grid, row, allEdges, "<b>All Edges</b>")
        row += 1
        for edge, title in edges:
            self.addHeading(grid, row, edge, f"<b>{title}</b>")
            row += 1
            for kind, name, unit in springs:
                self.addSpringRow(grid, row, join(edge, kind), name, unit)
                row += 1
        note = QLabel(edgesNote)
        note.setWordWrap(True)
        grid.addWidget(note, row, 0, 1, 6)

    def addHeading(self, grid: QGridLayout, row: int, key: str, title: str) -> None:
        grid.addWidget(richLabel(title), row, 0)
        # Above the column each one fills.
        grid.addWidget(self.buildConditionButton(key), row, 1)
        grid.addWidget(self.buildDampingButton(key), row, 3)

    def addSpringRow(self, grid: QGridLayout, row: int, path: str, name: str, unit: str) -> None:
        grid.addWidget(QLabel(name), row, 0)
        for column, part in ((1, "real"), (3, "imag")):
            spinBox = ScientificSpinBox()
            spinBox.setObjectName(path.replace("/", "_") + f"_{part}Input")
            spinBox.setMinimumWidth(110)
            spinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            spinBox.setKeyboardTracking(False)
            spinBox.valueChanged.connect(self.refreshButtons)
            grid.addWidget(spinBox, row, column)
            self.inputs[join(path, part)] = spinBox
        grid.addWidget(QLabel("+ j"), row, 2, Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel(unit), row, 4)

    def buildConditionButton(self, key: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName(f"{key}ConditionButton")
        button.setToolTip(conditionTip + (" on all four edges" if key == allEdges else ""))
        menu = QMenu(button)
        menu.setToolTipsVisible(True)
        for condition in EdgeCondition:
            action = menu.addAction(condition.label)
            action.setToolTip(conditionHelp[condition])
            action.triggered.connect(partial(self.conditionChosen.emit, key, condition))
        button.setMenu(menu)
        self.conditionButtons[key] = button
        return button

    def buildDampingButton(self, key: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName(f"{key}DampingButton")
        button.setToolTip(dampingTip + (" on all four edges" if key == allEdges else ""))
        menu = QMenu(button)
        for lossFactor in lossFactors:
            action = menu.addAction(lossFactorText(lossFactor))
            action.triggered.connect(partial(self.lossFactorChosen.emit, key, lossFactor))
        button.setMenu(menu)
        self.dampingButtons[key] = button
        return button

    def supports(self) -> PlateSupports:
        """The springs the inputs now hold."""
        return rebuild(
            PlateSupports(),
            lambda path: self.inputs[path].value() if path in self.inputs else None,
        )

    def refreshButtons(self, *_args: object) -> None:
        """Each button says what its edge's values now are; All Edges, what the four share."""
        supports = self.supports()
        conditions, levels = [], []
        for edge, _title in edges:
            condition = self.recognizeCondition(supports, edge)
            level = offeredLevel(lossFactorOf(supports, edge))
            conditions.append(condition)
            levels.append(level)
            self.conditionButtons[edge].setText(
                f"Condition: {condition.label if condition else 'Custom'}"
            )
            self.dampingButtons[edge].setText(
                f"Damping: {lossFactorText(level) if level is not None else 'Custom'}"
            )
        shared = conditions[0] if conditions[0] and len(set(conditions)) == 1 else None
        self.conditionButtons[allEdges].setText(
            f"Condition: {shared.label if shared else 'Mixed'}"
        )
        sharedLevel = levels[0] if levels[0] is not None and len(set(levels)) == 1 else None
        self.dampingButtons[allEdges].setText(
            f"Damping: {lossFactorText(sharedLevel) if sharedLevel is not None else 'Mixed'}"
        )

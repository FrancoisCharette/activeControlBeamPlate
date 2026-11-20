"""The End Supports group of Beam > Configuration > Parameters: the six springs.

One row per spring of Figure 2.1, grouped by end, each a complex stiffness
typed as its real part and its imaginary part (the damping), as Table 2.2
writes complex Young's moduli. Labelled with the figure's own symbols.

Each end has two buttons: Condition, above the real parts, fills
them with this app's recommended stiffnesses for Free, Pinned, Roller or
Clamped; Damping, above the imaginary parts, fills them with a loss factor
times the real parts. Both are worked out in beamEndConditions. Each button
says what the end's values are now: Condition names a support only while the
real parts are exactly what it would put there for the beam as it is, and
Damping a level only while every imaginary part is that level times its real
part. Anything else - a value typed by hand, a beam made longer - is Custom.
Which condition fits needs the beam, which this group does not have, so the
Parameters view hands it `recognizeCondition`.

The group only shows and reads the values, and says which button was used;
the Parameters view keeps the values and works out what a choice means.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QMenu, QPushButton, QWidget

from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.services.beamEndConditions import (
    EndCondition,
    conditionHelp,
    holdingFactor,
    lossFactorOf,
)
from activeControlBeamPlate.services.springDamping import lossFactors, lossFactorText
from activeControlBeamPlate.ui.widgets.scientificSpinBox import ScientificSpinBox

supportsNote = (
    "Each stiffness is its real part + j × its imaginary part, which is the damping. "
    "0 leaves the end free to move that way; a very large value holds it. Condition makes "
    f"a held spring {holdingFactor:,.0f} times the beam's own stiffness for that motion "
    "(EI/L³, EA/L, EI/L) - this app's recommendation; the thesis gives no values. "
    "Damping sets each imaginary part to the loss factor η × its real part."
)
conditionTip = "Fill this end's real parts with typical stiffnesses for a support"
dampingTip = (
    "Fill this end's imaginary parts with a loss factor η: imaginary = η × real, as Table 2.2 "
    "writes damping (the beam's own is 0.5 %)"
)


@dataclass(frozen=True)
class Spring:
    """One row: which BeamSupports field it edits and how it is labelled."""

    field: str
    name: str
    symbol: str  # as Figure 2.1 writes it, in rich text
    unit: str


ends = (
    ("left", "Left End, x = -L<sub>x</sub><sup>pt</sup>/2", (
        Spring("transverseLeft", "Transverse", "K<sub>V1</sub>", "N/m"),
        Spring("axialLeft", "Axial", "K<sub>H1</sub>", "N/m"),
        Spring("rotationalLeft", "Rotational", "K<sub>T1</sub>", "N·m/rad"),
    )),
    ("right", "Right End, x = L<sub>x</sub><sup>pt</sup>/2", (
        Spring("transverseRight", "Transverse", "K<sub>V2</sub>", "N/m"),
        Spring("axialRight", "Axial", "K<sub>H2</sub>", "N/m"),
        Spring("rotationalRight", "Rotational", "K<sub>T2</sub>", "N·m/rad"),
    )),
)


def richLabel(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.RichText)
    return label


class BeamSupportsBox(QGroupBox):
    # Any part of any spring was changed by the reader.
    changed = Signal()
    # A Boundary Condition was picked for an end: ("left" or "right", EndCondition).
    conditionChosen = Signal(str, object)
    # A Damping was picked for an end: ("left" or "right", loss factor).
    lossFactorChosen = Signal(str, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("End Supports", parent)
        self.inputs: dict[str, tuple[ScientificSpinBox, ScientificSpinBox]] = {}
        self.conditionButtons: dict[str, QPushButton] = {}
        self.dampingButtons: dict[str, QPushButton] = {}
        # Which condition an end's springs are, given the beam; set by the view
        # that knows the beam. Until then nothing is recognised.
        self.recognizeCondition: Callable[[BeamSupports, str], EndCondition | None] = (
            lambda _supports, _end: None
        )
        grid = QGridLayout(self)
        grid.setColumnStretch(5, 1)
        grid.addWidget(QLabel("Real Part"), 0, 1, Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel("Imaginary Part"), 0, 3, Qt.AlignmentFlag.AlignCenter)
        row = 1
        for end, endTitle, springs in ends:
            heading = richLabel(f"<b>{endTitle}</b>")
            grid.addWidget(heading, row, 0)
            # Above the column each one fills.
            grid.addWidget(self.buildConditionButton(end), row, 1)
            grid.addWidget(self.buildDampingButton(end), row, 3)
            row += 1
            for spring in springs:
                self.addSpringRow(grid, row, spring)
                row += 1
        note = QLabel(supportsNote)
        note.setWordWrap(True)
        grid.addWidget(note, row, 0, 1, 6)

    def addSpringRow(self, grid: QGridLayout, row: int, spring: Spring) -> None:
        real, imaginary = ScientificSpinBox(), ScientificSpinBox()
        for part, spinBox in (("Real", real), ("Imaginary", imaginary)):
            spinBox.setObjectName(f"{spring.field}{part}Input")
            spinBox.setMinimumWidth(110)
            spinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            spinBox.setKeyboardTracking(False)
            spinBox.valueChanged.connect(self.changed)
            spinBox.valueChanged.connect(self.refreshButtons)
        label = richLabel(f"{spring.name}, {spring.symbol}")
        label.setBuddy(real)
        grid.addWidget(label, row, 0)
        grid.addWidget(real, row, 1)
        grid.addWidget(QLabel("+ j"), row, 2, Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(imaginary, row, 3)
        grid.addWidget(QLabel(spring.unit), row, 4)
        self.inputs[spring.field] = (real, imaginary)

    def buildConditionButton(self, end: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName(f"{end}ConditionButton")
        button.setToolTip(conditionTip)
        menu = QMenu(button)
        menu.setToolTipsVisible(True)
        for condition in EndCondition:
            action = menu.addAction(condition.label)
            action.setToolTip(conditionHelp[condition])
            action.triggered.connect(partial(self.conditionChosen.emit, end, condition))
        button.setMenu(menu)
        self.conditionButtons[end] = button
        return button

    def buildDampingButton(self, end: str) -> QPushButton:
        button = QPushButton()
        button.setObjectName(f"{end}DampingButton")
        button.setToolTip(dampingTip)
        menu = QMenu(button)
        for lossFactor in lossFactors:
            action = menu.addAction(lossFactorText(lossFactor))
            action.triggered.connect(partial(self.lossFactorChosen.emit, end, lossFactor))
        button.setMenu(menu)
        self.dampingButtons[end] = button
        return button

    def refreshButtons(self, *_args: object) -> None:
        """Each button says what its end's values now are."""
        supports = self.supports()
        for end, button in self.conditionButtons.items():
            condition = self.recognizeCondition(supports, end)
            button.setText(f"Condition: {condition.label if condition else 'Custom'}")
            lossFactor = lossFactorOf(supports, end)
            offered = lossFactor is not None and any(
                abs(lossFactor - level) < 1e-9 for level in lossFactors
            )
            text = lossFactorText(lossFactor) if offered else "Custom"
            self.dampingButtons[end].setText(f"Damping: {text}")

    def supports(self) -> BeamSupports:
        """The springs the inputs now hold."""
        return replace(
            BeamSupports(),
            **{field: complex(real.value(), imaginary.value())
               for field, (real, imaginary) in self.inputs.items()},
        )

    def showSupports(self, supports: BeamSupports) -> None:
        """Put `supports` in the inputs without each one counting as a change."""
        for field, (real, imaginary) in self.inputs.items():
            stiffness: complex = getattr(supports, field)
            for spinBox, value in ((real, stiffness.real), (imaginary, stiffness.imag)):
                spinBox.blockSignals(True)
                spinBox.setValue(value)
                spinBox.blockSignals(False)
        self.refreshButtons()

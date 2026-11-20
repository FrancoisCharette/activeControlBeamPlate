"""The End Supports group of Beam > Configuration > Parameters: the six springs.

One row per spring of Figure 2.1, grouped by end, each a complex stiffness
typed as its real part and its imaginary part (the damping), as Table 2.2
writes complex Young's moduli. Labelled with the figure's own symbols. The
group only shows and reads the values; the Parameters view keeps them.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QWidget

from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.ui.widgets.scientificSpinBox import ScientificSpinBox

supportsNote = (
    "Each stiffness is its real part + j × its imaginary part, which is the damping. "
    "0 leaves the end free to move that way; a very large value holds it."
)


@dataclass(frozen=True)
class Spring:
    """One row: which BeamSupports field it edits and how it is labelled."""

    field: str
    name: str
    symbol: str  # as Figure 2.1 writes it, in rich text
    unit: str


ends = (
    ("Left End, x = -L<sub>x</sub><sup>pt</sup>/2", (
        Spring("transverseLeft", "Transverse", "K<sub>V1</sub>", "N/m"),
        Spring("axialLeft", "Axial", "K<sub>H1</sub>", "N/m"),
        Spring("rotationalLeft", "Rotational", "K<sub>T1</sub>", "N·m/rad"),
    )),
    ("Right End, x = L<sub>x</sub><sup>pt</sup>/2", (
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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("End Supports", parent)
        self.inputs: dict[str, tuple[ScientificSpinBox, ScientificSpinBox]] = {}
        grid = QGridLayout(self)
        grid.setColumnStretch(5, 1)
        grid.addWidget(QLabel("Real Part"), 0, 1, Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(QLabel("Imaginary Part"), 0, 3, Qt.AlignmentFlag.AlignCenter)
        row = 1
        for endTitle, springs in ends:
            heading = richLabel(f"<b>{endTitle}</b>")
            grid.addWidget(heading, row, 0, 1, 5)
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
        label = richLabel(f"{spring.name}, {spring.symbol}")
        label.setBuddy(real)
        grid.addWidget(label, row, 0)
        grid.addWidget(real, row, 1)
        grid.addWidget(QLabel("+ j"), row, 2, Qt.AlignmentFlag.AlignCenter)
        grid.addWidget(imaginary, row, 3)
        grid.addWidget(QLabel(spring.unit), row, 4)
        self.inputs[spring.field] = (real, imaginary)

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

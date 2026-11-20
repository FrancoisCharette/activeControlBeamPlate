"""The Materials group of Beam > Configuration > Parameters: Table 2.2's other rows.

One row per material property, one column per part, as Table 2.2 prints them;
a property a part does not have - the beam is not piezoelectric - shows a
dash. The columns follow the Beam, Actuator, Sensor groups above them on the
page. Each input is named by its path in BeamMaterials ("sensorDzx",
"beamYoungsModulus/imag"), which is also its settings key. The group only
shows and reads the values; the Parameters view keeps them.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDoubleSpinBox, QGridLayout, QGroupBox, QLabel, QWidget

from activeControlBeamPlate.models.beamMaterials import BeamMaterials
from activeControlBeamPlate.services.flatValues import flatten, rebuild
from activeControlBeamPlate.ui.widgets.scientificSpinBox import ScientificSpinBox

columns = (("beam", "Beam"), ("actuator", "Actuator"), ("sensor", "Sensor"))
materialsNote = (
    "As in Table 2.2. Young's modulus is complex: its imaginary part is the damping. "
    "e<sub>zx</sub> is close to d<sub>zx</sub> × Y (equation 2.24). Values such as 190e-12 "
    "can be typed in that form."
)


@dataclass(frozen=True)
class Row:
    """One row of Table 2.2: the path of its value for each part that has it."""

    label: str  # rich text, with the unit
    paths: dict[str, str]  # part -> path in BeamMaterials
    minimum: float = 0.0
    maximum: float = 1e15
    decimals: int | None = None  # None: scientific notation


rows = (
    Row("Density, ρ (kg/m³)", {part: f"{part}Density" for part, _ in columns},
        maximum=1e5, decimals=1),
    Row("Young's Modulus, Y, Real Part (N/m²)",
        {part: f"{part}YoungsModulus/real" for part, _ in columns}),
    Row("Young's Modulus, Y, Imaginary Part (N/m²)",
        {part: f"{part}YoungsModulus/imag" for part, _ in columns}),
    Row("Permittivity, ξ (F/m)", {"sensor": "sensorPermittivity"}, maximum=1.0),
    Row("d<sub>zx</sub> (m/V)", {"actuator": "actuatorDzx", "sensor": "sensorDzx"},
        minimum=-1.0, maximum=1.0),
    Row("e<sub>zx</sub> (N/(V·m))", {"actuator": "actuatorEzx", "sensor": "sensorEzx"},
        minimum=-1e4, maximum=1e4, decimals=3),
)


def richLabel(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.RichText)
    return label


class BeamMaterialsBox(QGroupBox):
    # Any value was changed by the reader.
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Materials", parent)
        self.inputs: dict[str, QDoubleSpinBox] = {}
        grid = QGridLayout(self)
        grid.setColumnStretch(len(columns) + 1, 1)
        for index, (_part, title) in enumerate(columns, start=1):
            grid.addWidget(richLabel(f"<b>{title}</b>"), 0, index, Qt.AlignmentFlag.AlignCenter)
        for rowIndex, row in enumerate(rows, start=1):
            grid.addWidget(richLabel(row.label), rowIndex, 0)
            for index, (part, _title) in enumerate(columns, start=1):
                path = row.paths.get(part)
                if path is None:
                    grid.addWidget(QLabel("-"), rowIndex, index, Qt.AlignmentFlag.AlignCenter)
                    continue
                spinBox = self.buildInput(row)
                spinBox.setObjectName(path.replace("/", "_") + "Input")
                grid.addWidget(spinBox, rowIndex, index)
                self.inputs[path] = spinBox
        note = richLabel(materialsNote)
        note.setWordWrap(True)
        grid.addWidget(note, len(rows) + 1, 0, 1, len(columns) + 2)

    def buildInput(self, row: Row) -> QDoubleSpinBox:
        if row.decimals is None:
            spinBox = ScientificSpinBox()
        else:
            spinBox = QDoubleSpinBox()
            spinBox.setDecimals(row.decimals)
        spinBox.setRange(row.minimum, row.maximum)
        spinBox.setMinimumWidth(120)
        spinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        spinBox.setKeyboardTracking(False)
        spinBox.valueChanged.connect(self.changed)
        return spinBox

    def materials(self) -> BeamMaterials:
        """The materials the inputs now hold."""
        return rebuild(
            BeamMaterials(),
            lambda path: self.inputs[path].value() if path in self.inputs else None,
        )

    def showMaterials(self, materials: BeamMaterials) -> None:
        """Put `materials` in the inputs without each one counting as a change."""
        for path, value in flatten(materials).items():
            spinBox = self.inputs[path]
            spinBox.blockSignals(True)
            spinBox.setValue(value)
            spinBox.blockSignals(False)

"""The Parameters tab under Beam > Configuration: everything Figure 2.1 defines.

The dimensions - the lengths and positions the figure draws, and the width and
thicknesses the text beside it gives - in three groups side by side, Beam,
Actuator and Sensor, as Table 2.2 lays them out; and under them the six
springs that hold the ends of the beam (BeamSupportsBox). Each input carries
the figure's own symbol, so the Schematic tab is the key to this one.

Every change is kept at once (beamGeometryService, beamSupportsService), and
a line under the inputs says what is wrong while the values do not describe a
beam that can be built - a transducer longer than the beam, say.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.services import beamGeometryService, beamSupportsService
from activeControlBeamPlate.ui.beam.beamSupportsBox import BeamSupportsBox
from activeControlBeamPlate.ui.widgets.reportingView import ReportingView

problemColour = "#d64545"
maximumLength = 100_000.0  # mm: far beyond any beam on a bench, and still a typo guard
dimensionsNote = (
    "All dimensions in mm. The width L<sub>y</sub> is the same for the beam, the actuator "
    "and the sensor. Positions are of each transducer's centre, measured along x from the "
    "centre of the beam, where the figure puts the z axis; negative towards the left end."
)
positionTip = (
    "Of the transducer's centre, from the centre of the beam; negative towards the left end"
)


@dataclass(frozen=True)
class Dimension:
    """One input: which BeamGeometry field it edits and how it is labelled."""

    group: str
    field: str
    name: str
    symbol: str  # as Figure 2.1 and its text write it, in rich text
    decimals: int = 2
    isPosition: bool = False


dimensions = (
    Dimension("Beam", "beamLength", "Length", "L<sub>x</sub><sup>pt</sup>"),
    Dimension("Beam", "width", "Width", "L<sub>y</sub>", decimals=3),
    Dimension("Beam", "beamThickness", "Thickness", "L<sub>z</sub><sup>pt</sup>", decimals=3),
    Dimension("Actuator", "actuatorLength", "Length", "L<sub>x</sub><sup>a</sup>"),
    Dimension("Actuator", "actuatorThickness", "Thickness", "L<sub>z</sub><sup>a</sup>",
              decimals=3),
    Dimension("Actuator", "actuatorPosition", "Position", "x<sub>a</sub>", isPosition=True),
    Dimension("Sensor", "sensorLength", "Length", "L<sub>x</sub><sup>c</sup>"),
    Dimension("Sensor", "sensorThickness", "Thickness", "L<sub>z</sub><sup>c</sup>",
              decimals=3),
    Dimension("Sensor", "sensorPosition", "Position", "x<sub>c</sub>", isPosition=True),
)


class BeamParametersView(ReportingView):
    # The values as they now stand, whether or not they describe a buildable beam.
    geometryChanged = Signal(BeamGeometry)
    supportsChanged = Signal(BeamSupports)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.inputs: dict[str, QDoubleSpinBox] = {}

        content = QWidget()
        layout = QVBoxLayout(content)
        groupRow = QHBoxLayout()
        for group in dict.fromkeys(dimension.group for dimension in dimensions):
            groupRow.addWidget(self.buildGroup(group))
        layout.addLayout(groupRow)
        note = QLabel(dimensionsNote)
        note.setTextFormat(Qt.TextFormat.RichText)
        note.setWordWrap(True)
        layout.addWidget(note)

        self.supportsBox = BeamSupportsBox()
        layout.addWidget(self.supportsBox)

        self.problemLabel = QLabel()
        self.problemLabel.setWordWrap(True)
        self.problemLabel.setStyleSheet(f"color: {problemColour};")
        layout.addWidget(self.problemLabel)
        layout.addLayout(self.buildButtonRow())
        layout.addStretch()

        # Taller than a small window: it scrolls rather than squeezing the inputs.
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        scrollArea.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scrollArea)

        self.showValues(beamGeometryService.loadGeometry(), beamSupportsService.loadSupports())
        for spinBox in self.inputs.values():
            spinBox.valueChanged.connect(self.onGeometryEdited)
        self.supportsBox.changed.connect(self.onSupportsEdited)

    def buildGroup(self, group: str) -> QGroupBox:
        box = QGroupBox(group)
        form = QFormLayout(box)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        for dimension in dimensions:
            if dimension.group != group:
                continue
            spinBox = self.buildInput(dimension)
            label = QLabel(f"{dimension.name}, {dimension.symbol}")
            label.setTextFormat(Qt.TextFormat.RichText)
            label.setBuddy(spinBox)
            form.addRow(label, spinBox)
            self.inputs[dimension.field] = spinBox
        return box

    @staticmethod
    def buildInput(dimension: Dimension) -> QDoubleSpinBox:
        spinBox = QDoubleSpinBox()
        spinBox.setObjectName(f"{dimension.field}Input")
        spinBox.setDecimals(dimension.decimals)
        spinBox.setSuffix(" mm")
        spinBox.setMinimumWidth(110)
        spinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        if dimension.isPosition:
            spinBox.setRange(-maximumLength, maximumLength)
            spinBox.setToolTip(positionTip)
        else:
            spinBox.setRange(0.0, maximumLength)
        # One change when the typing is done, not one per keystroke.
        spinBox.setKeyboardTracking(False)
        return spinBox

    def buildButtonRow(self) -> QHBoxLayout:
        self.restoreButton = QPushButton("Restore Table 2.2 Values")
        self.restoreButton.setToolTip(
            "The beam of Table 2.2 of the thesis, used throughout chapter 2, with free ends "
            "(every spring 0) as in its experiments"
        )
        self.restoreButton.clicked.connect(self.onRestoreClicked)
        row = QHBoxLayout()
        row.addWidget(self.restoreButton)
        row.addStretch()
        return row

    def geometry(self) -> BeamGeometry:
        """The dimensions the inputs now hold."""
        return replace(
            BeamGeometry(),
            **{field: spinBox.value() for field, spinBox in self.inputs.items()},
        )

    def supports(self) -> BeamSupports:
        """The springs the inputs now hold."""
        return self.supportsBox.supports()

    def showValues(self, geometry: BeamGeometry, supports: BeamSupports) -> None:
        """Put the values in the inputs without each one counting as a change."""
        for field, spinBox in self.inputs.items():
            spinBox.blockSignals(True)
            spinBox.setValue(getattr(geometry, field))
            spinBox.blockSignals(False)
        self.supportsBox.showSupports(supports)
        self.showProblems()

    def showProblems(self) -> None:
        problems = (beamGeometryService.problemsWith(self.geometry())
                    + beamSupportsService.problemsWith(self.supports()))
        self.problemLabel.setText("\n".join(problems))
        self.problemLabel.setVisible(bool(problems))

    def onGeometryEdited(self, _value: float) -> None:
        geometry = self.geometry()
        beamGeometryService.saveGeometry(geometry)
        self.showProblems()
        self.geometryChanged.emit(geometry)

    def onSupportsEdited(self) -> None:
        supports = self.supports()
        beamSupportsService.saveSupports(supports)
        self.showProblems()
        self.supportsChanged.emit(supports)

    def onRestoreClicked(self) -> None:
        geometry, supports = BeamGeometry(), BeamSupports()
        self.showValues(geometry, supports)
        beamGeometryService.saveGeometry(geometry)
        beamSupportsService.saveSupports(supports)
        self.geometryChanged.emit(geometry)
        self.supportsChanged.emit(supports)
        self.reportStatus("Beam parameters set to Table 2.2, with free ends.")

"""The Parameters tab under Beam > Configuration: Figure 2.1 and Table 2.2.

The dimensions - the lengths and positions the figure draws, and the width and
thicknesses the text beside it gives - in three groups side by side, Beam,
Actuator and Sensor; under them Table 2.2's material rows (BeamMaterialsBox);
and under those the six springs that hold the ends of the beam
(BeamSupportsBox). Each input carries the thesis's own symbol, so the
Schematic tab is the key to this one.

Every change is kept at once (beamGeometryService, beamMaterialsService,
beamSupportsService), and
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
from activeControlBeamPlate.models.beamMaterials import BeamMaterials
from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.services import (
    beamEndConditions,
    beamGeometryService,
    beamMaterialsService,
    beamSupportsService,
    springDamping,
)
from activeControlBeamPlate.services.beamEndConditions import EndCondition, EndConditionError
from activeControlBeamPlate.ui.beam.beamMaterialsBox import BeamMaterialsBox
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
    materialsChanged = Signal(BeamMaterials)
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

        self.materialsBox = BeamMaterialsBox()
        layout.addWidget(self.materialsBox)
        self.supportsBox = BeamSupportsBox()
        self.supportsBox.recognizeCondition = self.recognizeCondition
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

        self.showValues(
            beamGeometryService.loadGeometry(),
            beamMaterialsService.loadMaterials(),
            beamSupportsService.loadSupports(),
        )
        for spinBox in self.inputs.values():
            spinBox.valueChanged.connect(self.onGeometryEdited)
        self.materialsBox.changed.connect(self.onMaterialsEdited)
        self.supportsBox.changed.connect(self.onSupportsEdited)
        self.supportsBox.conditionChosen.connect(self.onConditionChosen)
        self.supportsBox.lossFactorChosen.connect(self.onLossFactorChosen)

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
            "The beam, actuator and sensor of Table 2.2 of the thesis, dimensions and "
            "materials, with free ends (every spring 0) as in its experiments"
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

    def materials(self) -> BeamMaterials:
        """The materials the inputs now hold."""
        return self.materialsBox.materials()

    def supports(self) -> BeamSupports:
        """The springs the inputs now hold."""
        return self.supportsBox.supports()

    def showValues(
        self, geometry: BeamGeometry, materials: BeamMaterials, supports: BeamSupports
    ) -> None:
        """Put the values in the inputs without each one counting as a change."""
        for field, spinBox in self.inputs.items():
            spinBox.blockSignals(True)
            spinBox.setValue(getattr(geometry, field))
            spinBox.blockSignals(False)
        self.materialsBox.showMaterials(materials)
        self.supportsBox.showSupports(supports)
        self.showProblems()

    def showProblems(self) -> None:
        problems = (beamGeometryService.problemsWith(self.geometry())
                    + beamMaterialsService.problemsWith(self.materials())
                    + beamSupportsService.problemsWith(self.supports()))
        self.problemLabel.setText("\n".join(problems))
        self.problemLabel.setVisible(bool(problems))

    def onGeometryEdited(self, _value: float) -> None:
        geometry = self.geometry()
        beamGeometryService.saveGeometry(geometry)
        self.supportsBox.refreshButtons()
        self.showProblems()
        self.geometryChanged.emit(geometry)

    def onMaterialsEdited(self) -> None:
        materials = self.materials()
        beamMaterialsService.saveMaterials(materials)
        self.supportsBox.refreshButtons()
        self.showProblems()
        self.materialsChanged.emit(materials)

    def recognizeCondition(self, supports: BeamSupports, end: str) -> EndCondition | None:
        """The condition the end's springs are, for the beam as the inputs now describe it."""
        return beamEndConditions.conditionOf(supports, end, self.geometry(), self.materials())

    def onConditionChosen(self, end: str, condition: EndCondition) -> None:
        """Fill the end's real parts for `condition`, scaled to the beam as it now is."""
        try:
            supports = beamEndConditions.withCondition(
                self.supports(), end, condition, self.geometry(), self.materials()
            )
        except EndConditionError as error:
            # A nudge to fill something in, which the red line already names.
            self.reportStatus(str(error))
            return
        self.supportsBox.showSupports(supports)
        self.onSupportsEdited()
        self.reportStatus(f"{end.capitalize()} end set to {condition.label}.")

    def onLossFactorChosen(self, end: str, lossFactor: float) -> None:
        """Fill the end's imaginary parts: the loss factor times each real part."""
        supports = beamEndConditions.withLossFactor(self.supports(), end, lossFactor)
        self.supportsBox.showSupports(supports)
        self.onSupportsEdited()
        self.reportStatus(
            f"{end.capitalize()} end damped with a loss factor of "
            f"{springDamping.lossFactorText(lossFactor)}."
        )

    def onSupportsEdited(self) -> None:
        supports = self.supports()
        beamSupportsService.saveSupports(supports)
        self.showProblems()
        self.supportsChanged.emit(supports)

    def onRestoreClicked(self) -> None:
        geometry, materials, supports = BeamGeometry(), BeamMaterials(), BeamSupports()
        self.showValues(geometry, materials, supports)
        beamGeometryService.saveGeometry(geometry)
        beamMaterialsService.saveMaterials(materials)
        beamSupportsService.saveSupports(supports)
        self.geometryChanged.emit(geometry)
        self.materialsChanged.emit(materials)
        self.supportsChanged.emit(supports)
        self.reportStatus("Beam parameters set to Table 2.2, with free ends.")

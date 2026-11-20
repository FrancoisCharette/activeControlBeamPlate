"""The Parameters tab under Plate > Configuration: Figure 5.1 and Table 5.1.

Table 5.1 laid out as the thesis prints it - one row per property, one column
each for the primary actuator, the secondary actuator and the plate - and
under it the edge springs Figure 5.1 draws (PlateEdgesBox). Each input is
named by its path in PlateConfiguration ("primaryActuator/positionX"), which
is also its key in the settings file, so the page and the file cannot drift.

Every change is kept at once (plateConfigurationService), and a line under
the inputs says what is wrong while the values do not describe a plate that
can be built - an actuator past an edge, two actuators overlapping.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from activeControlBeamPlate.models.plateConfiguration import PlateConfiguration, PlateSupports
from activeControlBeamPlate.services import (
    plateConfigurationService,
    plateEdgeConditions,
    springDamping,
)
from activeControlBeamPlate.services.flatValues import flatten, join, rebuild
from activeControlBeamPlate.services.plateEdgeConditions import (
    EdgeCondition,
    EdgeConditionError,
)
from activeControlBeamPlate.ui.plate.plateEdgesBox import PlateEdgesBox, allEdges
from activeControlBeamPlate.ui.widgets.reportingView import ReportingView
from activeControlBeamPlate.ui.widgets.scientificSpinBox import ScientificSpinBox

problemColour = "#d64545"
maximumLength = 100_000.0  # mm
maximumModulus = 1e15  # N/m²: far above any solid, so 63e9 is never clipped
tableNote = (
    "As in Table 5.1. An actuator is a pair of identical piezoceramics at the same place, one "
    "on each face of the plate; its values are those of one of them. Positions are of each "
    "actuator's centre, from the centre of the plate: x along L<sub>x</sub>, y along "
    "L<sub>y</sub>. Young's modulus is complex: its imaginary part is the damping."
)


@dataclass(frozen=True)
class Row:
    """One row of Table 5.1: the path of its value under each column, and its input."""

    path: str
    label: str  # rich text, with the unit
    decimals: int = 2  # ignored for scientific rows
    minimum: float = 0.0
    maximum: float = maximumLength
    scientific: bool = False
    actuatorOnly: bool = False


rows = (
    Row("length", "Length, L<sub>x</sub> (mm)"),
    Row("width", "Width, L<sub>y</sub> (mm)"),
    Row("thickness", "Thickness, L<sub>z</sub> (mm)", decimals=3),
    Row("density", "Density, ρ (kg/m³)", decimals=1),
    Row("youngsModulus/real", "Young's Modulus, Y, Real Part (N/m²)",
        maximum=maximumModulus, scientific=True),
    Row("youngsModulus/imag", "Young's Modulus, Y, Imaginary Part (N/m²)",
        maximum=maximumModulus, scientific=True),
    Row("poissonRatio", "Poisson's Ratio, ν", decimals=3, minimum=-0.999, maximum=0.499),
    Row("ezx", "e<sub>zx</sub> (N/(V·m))", decimals=3, minimum=-1e4, maximum=1e4,
        actuatorOnly=True),
    Row("dzx", "d<sub>zx</sub> (m/V)", minimum=-1.0, maximum=1.0, scientific=True,
        actuatorOnly=True),
    Row("positionX", "Position, x<sub>a</sub> (mm)", minimum=-maximumLength, actuatorOnly=True),
    Row("positionY", "Position, y<sub>a</sub> (mm)", minimum=-maximumLength, actuatorOnly=True),
)
columns = (
    ("primaryActuator", "Primary Actuator"),
    ("secondaryActuator", "Secondary Actuator"),
    ("plate", "Plate"),
)


def richLabel(text: str) -> QLabel:
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.RichText)
    return label


class PlateParametersView(ReportingView):
    # The configuration as it now stands, whether or not it can be built.
    configurationChanged = Signal(PlateConfiguration)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Every input, by its path in PlateConfiguration.
        self.inputs: dict[str, QDoubleSpinBox] = {}

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(self.buildTable())
        note = richLabel(tableNote)
        note.setWordWrap(True)
        layout.addWidget(note)
        self.edgesBox = PlateEdgesBox()
        self.edgesBox.recognizeCondition = self.recognizeCondition
        for path, spinBox in self.edgesBox.inputs.items():
            self.inputs[join("supports", path)] = spinBox
        self.edgesBox.conditionChosen.connect(self.onConditionChosen)
        self.edgesBox.lossFactorChosen.connect(self.onLossFactorChosen)
        layout.addWidget(self.edgesBox)

        self.problemLabel = QLabel()
        self.problemLabel.setWordWrap(True)
        self.problemLabel.setStyleSheet(f"color: {problemColour};")
        layout.addWidget(self.problemLabel)
        layout.addLayout(self.buildButtonRow())
        layout.addStretch()

        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollArea.setFrameShape(QFrame.Shape.NoFrame)
        scrollArea.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scrollArea)

        self.showConfiguration(plateConfigurationService.loadConfiguration())
        for spinBox in self.inputs.values():
            spinBox.valueChanged.connect(self.onEdited)

    def buildTable(self) -> QGroupBox:
        box = QGroupBox("Plate and Actuators")
        grid = QGridLayout(box)
        grid.setColumnStretch(len(columns) + 1, 1)
        for index, (_field, title) in enumerate(columns, start=1):
            grid.addWidget(richLabel(f"<b>{title}</b>"), 0, index, Qt.AlignmentFlag.AlignCenter)
        for rowIndex, row in enumerate(rows, start=1):
            grid.addWidget(richLabel(row.label), rowIndex, 0)
            for index, (field, _title) in enumerate(columns, start=1):
                if row.actuatorOnly and field == "plate":
                    grid.addWidget(QLabel("-"), rowIndex, index, Qt.AlignmentFlag.AlignCenter)
                    continue
                spinBox = self.buildInput(row)
                path = join(field, row.path)
                spinBox.setObjectName(path.replace("/", "_") + "Input")
                grid.addWidget(spinBox, rowIndex, index)
                self.inputs[path] = spinBox
        return box

    @staticmethod
    def buildInput(row: Row) -> QDoubleSpinBox:
        spinBox = ScientificSpinBox() if row.scientific else QDoubleSpinBox()
        if not row.scientific:
            spinBox.setDecimals(row.decimals)
        spinBox.setRange(row.minimum, row.maximum)
        spinBox.setMinimumWidth(120)
        spinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
        # One change when the typing is done, not one per keystroke.
        spinBox.setKeyboardTracking(False)
        return spinBox

    def buildButtonRow(self) -> QHBoxLayout:
        self.restoreButton = QPushButton("Restore Table 5.1 Values")
        self.restoreButton.setToolTip(
            "The plate and actuators of Table 5.1 of the thesis, with every edge spring at 0"
        )
        self.restoreButton.clicked.connect(self.onRestoreClicked)
        row = QHBoxLayout()
        row.addWidget(self.restoreButton)
        row.addStretch()
        return row

    def configuration(self) -> PlateConfiguration:
        """The configuration the inputs now hold."""
        return rebuild(
            PlateConfiguration(),
            lambda path: self.inputs[path].value() if path in self.inputs else None,
        )

    def showConfiguration(self, configuration: PlateConfiguration) -> None:
        """Put `configuration` in the inputs without each one counting as a change."""
        for path, value in flatten(configuration).items():
            spinBox = self.inputs[path]
            spinBox.blockSignals(True)
            spinBox.setValue(value)
            spinBox.blockSignals(False)
        self.edgesBox.refreshButtons()
        self.showProblems(configuration)

    def showProblems(self, configuration: PlateConfiguration) -> None:
        problems = plateConfigurationService.problemsWith(configuration)
        self.problemLabel.setText("\n".join(problems))
        self.problemLabel.setVisible(bool(problems))

    def onEdited(self, _value: float) -> None:
        # A plate made thicker changes what each condition means, so the buttons
        # are redone whatever was edited.
        self.edgesBox.refreshButtons()
        self.applyConfiguration(self.configuration())

    def recognizeCondition(self, supports: PlateSupports, edge: str) -> EdgeCondition | None:
        """The condition the edge's springs are, for the plate as the inputs now describe it."""
        return plateEdgeConditions.conditionOf(supports, edge, self.configuration().plate)

    @staticmethod
    def edgesFor(key: str) -> tuple[str, ...]:
        return plateEdgeConditions.edges if key == allEdges else (key,)

    @staticmethod
    def edgeName(key: str) -> str:
        if key == allEdges:
            return "All edges"
        axis, sign = key[4].lower(), "-" if key.endswith("Negative") else "+"
        return f"Edge {axis} = {sign}L_{axis}/2"

    def onConditionChosen(self, key: str, condition: EdgeCondition) -> None:
        """Fill the edge's real parts - or all four edges' - scaled to the plate as it now is."""
        configuration = self.configuration()
        supports = configuration.supports
        try:
            for edge in self.edgesFor(key):
                supports = plateEdgeConditions.withCondition(
                    supports, edge, condition, configuration.plate
                )
        except EdgeConditionError as error:
            # A nudge to fill something in, which the red line already names.
            self.reportStatus(str(error))
            return
        self.applyEdges(supports)
        self.reportStatus(f"{self.edgeName(key)} set to {condition.label}.")

    def onLossFactorChosen(self, key: str, lossFactor: float) -> None:
        """Fill the edge's imaginary parts - or all four edges' - with the loss factor."""
        supports = self.configuration().supports
        for edge in self.edgesFor(key):
            supports = plateEdgeConditions.withLossFactor(supports, edge, lossFactor)
        self.applyEdges(supports)
        self.reportStatus(
            f"{self.edgeName(key)} damped with a loss factor of "
            f"{springDamping.lossFactorText(lossFactor)}."
        )

    def applyEdges(self, supports: PlateSupports) -> None:
        configuration = replace(self.configuration(), supports=supports)
        self.showConfiguration(configuration)
        self.applyConfiguration(configuration)

    def onRestoreClicked(self) -> None:
        configuration = PlateConfiguration()
        self.showConfiguration(configuration)
        self.applyConfiguration(configuration)
        self.reportStatus("Plate parameters set to Table 5.1, with free edges.")

    def applyConfiguration(self, configuration: PlateConfiguration) -> None:
        """Keep it, say what is wrong with it if anything, and tell whoever listens."""
        plateConfigurationService.saveConfiguration(configuration)
        self.showProblems(configuration)
        self.configurationChanged.emit(configuration)

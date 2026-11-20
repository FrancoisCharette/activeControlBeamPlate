"""The Actuation tab under Beam: how the actuator of Figure 2.1 is driven (chapter 2).

Three groups: the Excitation - asymmetric with the one actuator, or symmetric
with a second, identical one facing it on the lower surface, driven for pure
bending or pure extension; the Applied Voltage on the upper actuator; and the
Frequency Band the response is worked out over.

The actuator itself - its length, thickness, position and material - is on
Configuration > Parameters. That tab's dimensions are followed here
(`setGeometry`), because a symmetric excitation's lower element has to find
room beside the sensor.

Every change is kept at once (beamActuationService), and a line under the
inputs says what is wrong while the values cannot be used.
"""

from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from activeControlBeamPlate.models.beamActuation import BeamActuation, Excitation
from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.services import beamActuationService, beamGeometryService
from activeControlBeamPlate.ui.widgets.reportingView import ReportingView

problemColour = "#d64545"
excitationHelp = {
    Excitation.asymmetric: (
        "The one actuator of Figure 2.1, on the upper surface. It moves the beam axially "
        "and transversely at once - how Table 2.2's beam was driven."
    ),
    Excitation.pureBending: (
        "A second actuator, identical to the first, facing it on the lower surface and "
        "driven 180° out of phase: the beam bends only."
    ),
    Excitation.pureExtension: (
        "A second actuator, identical to the first, facing it on the lower surface and "
        "driven in phase: the beam stretches and shrinks only."
    ),
}
voltageNote = (
    "On the upper actuator. In a symmetric excitation the lower one gets the same amplitude, "
    "at the phase above plus 180° for pure bending, or the same phase for pure extension. "
    "The thesis's simulations use 1 V at 0°; its experiments drove the actuator with up to "
    "about 60 V."
)
# (field, label, unit, decimals, minimum, maximum)
voltageFields = (
    ("voltageAmplitude", "Amplitude, V", " V", 3, 0.0, 10_000.0),
    ("voltagePhase", "Phase, φ", " °", 1, -360.0, 360.0),
)
frequencyFields = (
    ("frequencyStart", "Start", " Hz", 2, 0.0, 1e6),
    ("frequencyEnd", "End", " Hz", 2, 0.0, 1e6),
    ("frequencyStep", "Step", " Hz", 3, 0.0, 1e6),
)


class BeamActuationView(ReportingView):
    # The actuation as it now stands, whether or not it can be used.
    actuationChanged = Signal(BeamActuation)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.beamGeometry: BeamGeometry = beamGeometryService.loadGeometry()
        self.inputs: dict[str, QDoubleSpinBox] = {}
        self.excitationButtons: dict[Excitation, QRadioButton] = {}

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.addWidget(self.buildExcitationGroup())
        layout.addWidget(self.buildNumberGroup("Applied Voltage", voltageFields, voltageNote))
        layout.addWidget(self.buildNumberGroup("Frequency Band", frequencyFields, None))
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

        self.showActuation(beamActuationService.loadActuation())
        for spinBox in self.inputs.values():
            spinBox.valueChanged.connect(self.onEdited)
        self.excitationGroup.idToggled.connect(self.onExcitationToggled)

    def buildExcitationGroup(self) -> QGroupBox:
        box = QGroupBox("Excitation")
        layout = QVBoxLayout(box)
        self.excitationGroup = QButtonGroup(box)
        for index, excitation in enumerate(Excitation):
            button = QRadioButton(excitation.label)
            button.setObjectName(f"{excitation.name}Button")
            description = QLabel(excitationHelp[excitation])
            description.setWordWrap(True)
            description.setIndent(24)  # under the label, past the radio button
            layout.addWidget(button)
            layout.addWidget(description)
            self.excitationGroup.addButton(button, index)
            self.excitationButtons[excitation] = button
        return box

    def buildNumberGroup(self, title: str, fields: tuple, note: str | None) -> QGroupBox:
        box = QGroupBox(title)
        form = QFormLayout(box)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        for field, label, unit, decimals, minimum, maximum in fields:
            spinBox = QDoubleSpinBox()
            spinBox.setObjectName(f"{field}Input")
            spinBox.setDecimals(decimals)
            spinBox.setRange(minimum, maximum)
            spinBox.setSuffix(unit)
            spinBox.setMinimumWidth(140)
            spinBox.setAlignment(Qt.AlignmentFlag.AlignRight)
            # One change when the typing is done, not one per keystroke.
            spinBox.setKeyboardTracking(False)
            form.addRow(label, spinBox)
            self.inputs[field] = spinBox
        if note:
            noteLabel = QLabel(note)
            noteLabel.setWordWrap(True)
            form.addRow(noteLabel)
        if fields is frequencyFields:
            self.countLabel = QLabel()
            form.addRow(self.countLabel)
        return box

    def buildButtonRow(self) -> QHBoxLayout:
        self.restoreButton = QPushButton("Restore Default Values")
        self.restoreButton.setToolTip(
            "Asymmetric, 1 V at 0°, 1 to 3200 Hz in steps of 1 Hz: the thesis's simulations "
            "and the band of chapter 2's figures"
        )
        self.restoreButton.clicked.connect(self.onRestoreClicked)
        row = QHBoxLayout()
        row.addWidget(self.restoreButton)
        row.addStretch()
        return row

    def actuation(self) -> BeamActuation:
        """The actuation the inputs now hold."""
        checked = self.excitationGroup.checkedId()
        excitation = list(Excitation)[checked] if checked >= 0 else Excitation.asymmetric
        return replace(
            BeamActuation(excitation=excitation),
            **{field: spinBox.value() for field, spinBox in self.inputs.items()},
        )

    def showActuation(self, actuation: BeamActuation) -> None:
        """Put `actuation` in the inputs without each one counting as a change."""
        self.excitationGroup.blockSignals(True)
        self.excitationButtons[actuation.excitation].setChecked(True)
        self.excitationGroup.blockSignals(False)
        for field, spinBox in self.inputs.items():
            spinBox.blockSignals(True)
            spinBox.setValue(getattr(actuation, field))
            spinBox.blockSignals(False)
        self.showState(actuation)

    def setGeometry(self, geometry: BeamGeometry) -> None:
        """The beam's dimensions changed on the Parameters tab."""
        self.beamGeometry = geometry
        self.showState(self.actuation())

    def showState(self, actuation: BeamActuation) -> None:
        count = beamActuationService.frequencyCount(actuation)
        self.countLabel.setText(
            f"{count:,} frequencies, from {actuation.frequencyStart:g} Hz."
            if count else "No frequencies in this band."
        )
        problems = beamActuationService.problemsWith(actuation, self.beamGeometry)
        self.problemLabel.setText("\n".join(problems))
        self.problemLabel.setVisible(bool(problems))

    def onEdited(self, *_args: object) -> None:
        self.applyActuation(self.actuation())

    def onExcitationToggled(self, _id: int, checked: bool) -> None:
        if checked:  # the button turned off says nothing new
            self.applyActuation(self.actuation())

    def onRestoreClicked(self) -> None:
        actuation = BeamActuation()
        self.showActuation(actuation)
        self.applyActuation(actuation)
        self.reportStatus("Beam actuation set to the default values.")

    def applyActuation(self, actuation: BeamActuation) -> None:
        """Keep it, say what is wrong with it if anything, and tell whoever listens."""
        beamActuationService.saveActuation(actuation)
        self.showState(actuation)
        self.actuationChanged.emit(actuation)

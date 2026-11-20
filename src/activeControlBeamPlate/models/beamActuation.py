"""How the beam's actuator is driven: chapter 2 of the thesis.

The A.C.P.A. model of chapter 2 gives the beam's response to a voltage at
angular frequency ω applied to the piezoceramic of Figure 2.1 (eq. 2.29).
With that one element on the upper surface the excitation is asymmetric: it
moves the beam axially and transversely at once. A second, identical element
facing it on the lower surface makes it symmetric - pure bending when the two
are driven 180° apart, pure extension when they are driven in phase.

The voltage is the upper element's: an amplitude in volts and a phase in
degrees. The frequency band is the range of ω/2π the response is worked out
over, in Hz.

The defaults: asymmetric, as Table 2.2's beam was driven; 1 V at 0°, the
voltage of the thesis's simulations (section 4.4); and 1 to 3200 Hz in 1 Hz
steps - chapter 2's figures run to 3200 Hz, and a free-free beam has no
static response at 0 Hz to compute.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Excitation(Enum):
    """What drives the beam: (label, lower element's phase relative to the upper, if any)."""

    asymmetric = ("Asymmetric", None)
    pureBending = ("Symmetric, Pure Bending", 180.0)
    pureExtension = ("Symmetric, Pure Extension", 0.0)

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def lowerPhaseShift(self) -> float | None:
        """The lower element's phase relative to the upper one; None with no lower element."""
        return self.value[1]

    @property
    def isSymmetric(self) -> bool:
        return self.lowerPhaseShift is not None


@dataclass(frozen=True)
class BeamActuation:
    excitation: Excitation = Excitation.asymmetric
    voltageAmplitude: float = 1.0  # V
    voltagePhase: float = 0.0  # degrees
    frequencyStart: float = 1.0  # Hz
    frequencyEnd: float = 3200.0  # Hz
    frequencyStep: float = 1.0  # Hz

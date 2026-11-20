"""The materials of the beam system of Table 2.2 of the thesis.

The rows of Table 2.2 that are not dimensions: each part's density and
Young's modulus, the sensor's permittivity, and the piezoelectric constants
of the actuator (a piezoceramic) and the sensor (a PVDF film). The beam is
not piezoelectric, so it has no constants, and only the sensor's permittivity
is given.

Density in kg/m³; Young's modulus in N/m², complex - the imaginary part is
the damping, written in Table 2.2 as the second of a pair; permittivity ξ in
F/m; d_zx in m/V; e_zx in N/(V·m). The table's e_zx are close to d_zx × Y
(equation 2.24), the approximation used when a maker gives only d_zx.

The defaults are Table 2.2.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BeamMaterials:
    beamDensity: float = 2726.0
    beamYoungsModulus: complex = 71e9 + 35.5e7j
    actuatorDensity: float = 7614.0
    actuatorYoungsModulus: complex = 63e9 + 0j
    actuatorDzx: float = 190e-12
    actuatorEzx: float = 12.0
    sensorDensity: float = 3400.0
    sensorYoungsModulus: complex = 2e9 + 0j
    sensorPermittivity: float = 106e-12  # ξ
    sensorDzx: float = 23e-12
    sensorEzx: float = 0.046

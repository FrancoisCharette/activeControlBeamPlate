"""The dimensions of the beam system of Figure 2.1 of the thesis.

Figure 2.1 shows a beam with a piezoceramic actuator on its upper surface and
a PVDF sensor on its lower surface. It draws the length of each of the three
and where the actuator and the sensor sit along the beam; the text beside it
adds the width, L_y, which is the same for all three, and their thicknesses,
L_z.

Lengths are along x. A position is the x coordinate of a transducer's centre,
measured from the centre of the beam, where the figure puts the z axis; it is
negative towards the left end. All values are in millimetres.

The defaults are the configuration of Table 2.2, used throughout chapter 2.
"""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class BeamGeometry:
    beamLength: float = 295.0  # L_x^pt
    width: float = 12.65  # L_y, shared by the beam, the actuator and the sensor
    beamThickness: float = 3.25  # L_z^pt
    actuatorLength: float = 25.38  # L_x^a
    actuatorThickness: float = 0.18  # L_z^a
    actuatorPosition: float = 131.0  # x_a
    sensorLength: float = 295.0  # L_x^c
    sensorThickness: float = 0.11  # L_z^c
    sensorPosition: float = 0.0  # x_c

    @staticmethod
    def fieldNames() -> list[str]:
        """The dimensions in the order they are stored."""
        return [field.name for field in fields(BeamGeometry)]

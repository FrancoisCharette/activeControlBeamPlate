"""The springs that hold the ends of the beam in Figure 2.1 of the thesis.

Each end of the beam is attached to a rigid support by three springs, whose
potential energy is equation 2.25: K_V against the transverse displacement w,
K_H against the axial displacement u, and K_T against the rotation dw/dx.
Index 1 is the left end, x = -L_x^pt / 2, and index 2 the right end.

The stiffnesses are complex: the imaginary part is the damping, as for the
complex Young's moduli of Table 2.2. Setting them models any boundary
condition - 0 leaves an end free, a very large value holds it. K_V and K_H
are in N/m, K_T in N·m/rad.

The defaults are all 0, a free-free beam: the condition of the experiments
of chapter 2 on the beam of Table 2.2.
"""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class BeamSupports:
    transverseLeft: complex = 0j  # K_V1, N/m
    axialLeft: complex = 0j  # K_H1, N/m
    rotationalLeft: complex = 0j  # K_T1, N·m/rad
    transverseRight: complex = 0j  # K_V2, N/m
    axialRight: complex = 0j  # K_H2, N/m
    rotationalRight: complex = 0j  # K_T2, N·m/rad

    @staticmethod
    def fieldNames() -> list[str]:
        """The springs in the order they are stored."""
        return [field.name for field in fields(BeamSupports)]

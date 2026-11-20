"""The plate system of Figure 5.1 and Table 5.1 of the thesis.

A thin, homogeneous, rectangular plate held along each edge by distributed
line springs, driven by piezoelectric actuators. Each actuator is a pair of
identical piezoceramic elements at the same place, one on each face, driven
180° apart (pure bending); its values are those of one element.

Positions are of an actuator's centre, in the centred coordinate system of
chapter 5: from the centre of the plate, x along its length L_x and y along
its width L_y. Lengths are in mm, density in kg/m³, Young's modulus in N/m²
(complex: the imaginary part is the damping), e_zx in N/(V·m), d_zx in m/V.

The defaults are Table 5.1, the simply supported plate of chapter 5 with its
primary and secondary actuators. The thesis gives no values for the edge
springs, so they start at 0 - free edges - and the reader sets them.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlateProperties:
    length: float = 480.0  # L_x
    width: float = 420.0  # L_y
    thickness: float = 3.22  # L_z
    density: float = 2700.0  # ρ
    youngsModulus: complex = 66.5e9 + 33e7j  # Y
    poissonRatio: float = 0.33  # ν


@dataclass(frozen=True)
class PlateActuator:
    """One actuator: a pair of identical piezoceramics, so the values of one of them."""

    length: float = 38.1  # L_x
    width: float = 31.8  # L_y
    thickness: float = 0.254  # L_z
    density: float = 7750.0  # ρ
    youngsModulus: complex = 63e9 + 0j  # Y
    poissonRatio: float = 0.33  # ν
    ezx: float = 14.0  # e_zx
    dzx: float = 210e-12  # d_zx
    positionX: float = 0.0  # x_a
    positionY: float = 0.0  # y_a


@dataclass(frozen=True)
class EdgeSupport:
    """The springs along one edge, per metre of edge (complex, like the beam's).

    Transverse resists the edge moving out of the plane, in N/m²; rotational
    resists it turning about itself, in N/rad (N·m/rad per m).
    """

    transverse: complex = 0j
    rotational: complex = 0j


@dataclass(frozen=True)
class PlateSupports:
    edgeXNegative: EdgeSupport = field(default_factory=EdgeSupport)  # x = -L_x/2
    edgeXPositive: EdgeSupport = field(default_factory=EdgeSupport)  # x = +L_x/2
    edgeYNegative: EdgeSupport = field(default_factory=EdgeSupport)  # y = -L_y/2
    edgeYPositive: EdgeSupport = field(default_factory=EdgeSupport)  # y = +L_y/2


@dataclass(frozen=True)
class PlateConfiguration:
    plate: PlateProperties = field(default_factory=PlateProperties)
    primaryActuator: PlateActuator = field(
        default_factory=lambda: PlateActuator(positionX=-69.0, positionY=86.1)
    )
    secondaryActuator: PlateActuator = field(
        default_factory=lambda: PlateActuator(positionX=-39.5, positionY=-35.6)
    )
    supports: PlateSupports = field(default_factory=PlateSupports)

"""Checks and keeps the plate configuration of Figure 5.1 and Table 5.1.

Kept in the settings file under "plate/", one key per number (flatValues), so
what is typed on Plate > Configuration > Parameters is there the next time the
app starts. What is kept is what was typed, even when it does not describe a
plate that can be built; the checks say what is wrong.
"""

from __future__ import annotations

import logging

from activeControlBeamPlate.models.plateConfiguration import (
    PlateActuator,
    PlateConfiguration,
    PlateProperties,
)
from activeControlBeamPlate.services import settingsService
from activeControlBeamPlate.services.flatValues import flatten, rebuild

logger = logging.getLogger(__name__)

settingsGroup = "plate"
# Rounding in an input must not make an actuator that ends exactly at an edge
# look as if it runs past it.
tolerance = 1e-9
actuatorNames = {"primaryActuator": "primary actuator", "secondaryActuator": "secondary actuator"}
edgeNames = {
    "edgeXNegative": "edge x = -L_x/2",
    "edgeXPositive": "edge x = +L_x/2",
    "edgeYNegative": "edge y = -L_y/2",
    "edgeYPositive": "edge y = +L_y/2",
}


def materialProblems(name: str, part: PlateProperties | PlateActuator) -> list[str]:
    problems = [
        f"The {name} {quantity} must be greater than zero."
        for quantity, value in (
            ("length", part.length),
            ("width", part.width),
            ("thickness", part.thickness),
            ("density", part.density),
            ("Young's modulus", part.youngsModulus.real),
        )
        if value <= 0
    ]
    if part.youngsModulus.imag < 0:
        problems.append(f"The damping of the {name} Young's modulus cannot be negative.")
    if not -1 < part.poissonRatio < 0.5:
        problems.append(f"The {name} Poisson's ratio must be between -1 and 0.5.")
    return problems


def span(centre: float, size: float) -> tuple[float, float]:
    return centre - size / 2, centre + size / 2


def placementProblems(name: str, actuator: PlateActuator, plate: PlateProperties) -> list[str]:
    """Whether the actuator lies on the plate, in x and in y."""
    problems = []
    for axis, centre, size, plateSize in (
        ("x", actuator.positionX, actuator.length, plate.length),
        ("y", actuator.positionY, actuator.width, plate.width),
    ):
        start, end = span(centre, size)
        half = plateSize / 2
        if start < -half - tolerance or end > half + tolerance:
            problems.append(
                f"The {name} runs past the edge of the plate in {axis}: it spans {axis} = "
                f"{start:g} to {end:g} mm, and the plate {axis} = {-half:g} to {half:g} mm."
            )
    return problems


def overlaps(first: PlateActuator, second: PlateActuator) -> bool:
    """Whether the two cover some of the same area (touching edges do not count)."""
    for centre1, size1, centre2, size2 in (
        (first.positionX, first.length, second.positionX, second.length),
        (first.positionY, first.width, second.positionY, second.width),
    ):
        start1, end1 = span(centre1, size1)
        start2, end2 = span(centre2, size2)
        if end1 <= start2 + tolerance or end2 <= start1 + tolerance:
            return False
    return True


def problemsWith(configuration: PlateConfiguration) -> list[str]:
    """Each way the configuration fails to describe a plate that can be built; empty if none."""
    plate = configuration.plate
    problems = materialProblems("plate", plate)
    actuators = {name: getattr(configuration, name) for name in actuatorNames}
    for field, actuator in actuators.items():
        problems += materialProblems(actuatorNames[field], actuator)
        if plate.length > 0 and plate.width > 0 and actuator.length > 0 and actuator.width > 0:
            problems += placementProblems(actuatorNames[field], actuator, plate)
    if overlaps(*actuators.values()):
        problems.append(
            "The primary and secondary actuators overlap; they cannot share the plate's surface."
        )
    for field, name in edgeNames.items():
        edge = getattr(configuration.supports, field)
        for kind, stiffness in (("transverse", edge.transverse), ("rotational", edge.rotational)):
            if stiffness.real < 0:
                problems.append(f"The {kind} stiffness of the {name} cannot be negative.")
            if stiffness.imag < 0:
                problems.append(f"The {kind} damping of the {name} cannot be negative.")
    return problems


def loadConfiguration() -> PlateConfiguration:
    """The configuration last saved, with Table 5.1's value for anything missing or unreadable."""
    settings = settingsService.openSettings()

    def read(path: str) -> float | None:
        value = settings.value(f"{settingsGroup}/{path}")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            logger.warning("Ignoring unreadable saved plate value %s: %r", path, value)
            return None

    return rebuild(PlateConfiguration(), read)


def saveConfiguration(configuration: PlateConfiguration) -> None:
    settingsService.writeValues(
        {f"{settingsGroup}/{path}": value for path, value in flatten(configuration).items()}
    )

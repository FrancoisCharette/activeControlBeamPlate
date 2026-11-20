"""Checks and keeps the beam dimensions of Figure 2.1.

The dimensions are kept in the settings file, so the values typed on the
Parameters tab are there the next time the app starts. What is kept is what
was typed, even when it does not describe a beam that can exist; the checks
say what is wrong, and the reader fixes it.
"""

from __future__ import annotations

import logging
from dataclasses import replace

from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.services import settingsService

logger = logging.getLogger(__name__)

settingsGroup = "beam/geometry"
# Rounding in a spin box must not make a transducer that ends exactly at the
# end of the beam - the sensor of Table 2.2 does - look as if it runs past it.
tolerance = 1e-9


def problemsWith(geometry: BeamGeometry) -> list[str]:
    """Each way the dimensions fail to describe a beam that can be built; empty if none."""
    problems: list[str] = []
    for name, size in (
        ("beam length", geometry.beamLength),
        ("width", geometry.width),
        ("beam thickness", geometry.beamThickness),
        ("actuator length", geometry.actuatorLength),
        ("actuator thickness", geometry.actuatorThickness),
        ("sensor length", geometry.sensorLength),
        ("sensor thickness", geometry.sensorThickness),
    ):
        if size <= 0:
            problems.append(f"The {name} must be greater than zero.")
    if geometry.beamLength <= 0:
        return problems
    halfBeam = geometry.beamLength / 2
    for name, length, position in (
        ("actuator", geometry.actuatorLength, geometry.actuatorPosition),
        ("sensor", geometry.sensorLength, geometry.sensorPosition),
    ):
        if length <= 0:
            continue
        start, end = position - length / 2, position + length / 2
        if start < -halfBeam - tolerance or end > halfBeam + tolerance:
            problems.append(
                f"The {name} runs past the end of the beam: it spans x = {start:g} to "
                f"{end:g} mm, and the beam spans x = {-halfBeam:g} to {halfBeam:g} mm."
            )
    return problems


def loadGeometry() -> BeamGeometry:
    """The dimensions last saved, with Table 2.2's value for any that is missing or unreadable."""
    settings = settingsService.openSettings()
    geometry = BeamGeometry()
    for name in BeamGeometry.fieldNames():
        value = settings.value(f"{settingsGroup}/{name}")
        if value is None:
            continue
        try:
            geometry = replace(geometry, **{name: float(value)})
        except (TypeError, ValueError):
            logger.warning("Ignoring unreadable saved %s: %r", name, value)
    return geometry


def saveGeometry(geometry: BeamGeometry) -> None:
    for name in BeamGeometry.fieldNames():
        settingsService.writeValue(f"{settingsGroup}/{name}", getattr(geometry, name))

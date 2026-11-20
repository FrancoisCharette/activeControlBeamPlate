"""Checks and keeps the beam materials of Table 2.2.

Kept in the settings file under "beam/materials/", one key per number
(flatValues: a complex Young's modulus is "<name>/real" and "<name>/imag"),
so what is typed on Beam > Configuration > Parameters is there next time.
"""

from __future__ import annotations

import logging

from activeControlBeamPlate.models.beamMaterials import BeamMaterials
from activeControlBeamPlate.services import settingsService
from activeControlBeamPlate.services.flatValues import flatten, rebuild

logger = logging.getLogger(__name__)

settingsGroup = "beam/materials"
parts = ("beam", "actuator", "sensor")


def problemsWith(materials: BeamMaterials) -> list[str]:
    """Each value no real material has; empty if none.

    The piezoelectric constants are left alone: their sign depends on how the
    element is poled and wired, so either sign is a real element.
    """
    problems: list[str] = []
    for part in parts:
        density = getattr(materials, f"{part}Density")
        modulus: complex = getattr(materials, f"{part}YoungsModulus")
        if density <= 0:
            problems.append(f"The {part} density must be greater than zero.")
        if modulus.real <= 0:
            problems.append(f"The {part} Young's modulus must be greater than zero.")
        if modulus.imag < 0:
            problems.append(f"The damping of the {part} Young's modulus cannot be negative.")
    if materials.sensorPermittivity <= 0:
        problems.append("The sensor permittivity must be greater than zero.")
    return problems


def loadMaterials() -> BeamMaterials:
    """The materials last saved, with Table 2.2's value for anything missing or unreadable."""
    settings = settingsService.openSettings()

    def read(path: str) -> float | None:
        value = settings.value(f"{settingsGroup}/{path}")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            logger.warning("Ignoring unreadable saved beam material %s: %r", path, value)
            return None

    return rebuild(BeamMaterials(), read)


def saveMaterials(materials: BeamMaterials) -> None:
    settingsService.writeValues(
        {f"{settingsGroup}/{path}": value for path, value in flatten(materials).items()}
    )

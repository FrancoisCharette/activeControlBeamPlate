"""Checks and keeps the end springs of the beam of Figure 2.1.

Kept in the settings file like the dimensions (beamGeometryService), so the
values typed on the Parameters tab are there the next time the app starts.
Each spring is stored as its real and its imaginary part.
"""

from __future__ import annotations

import logging
from dataclasses import replace

from activeControlBeamPlate.models.beamSupports import BeamSupports
from activeControlBeamPlate.services import settingsService

logger = logging.getLogger(__name__)

settingsGroup = "beam/supports"
# How each spring is named in a message: the end, what it resists, its symbol.
springNames = {
    "transverseLeft": "left transverse spring, K_V1",
    "axialLeft": "left axial spring, K_H1",
    "rotationalLeft": "left rotational spring, K_T1",
    "transverseRight": "right transverse spring, K_V2",
    "axialRight": "right axial spring, K_H2",
    "rotationalRight": "right rotational spring, K_T2",
}


def problemsWith(supports: BeamSupports) -> list[str]:
    """Each spring that is not a passive one; empty if none.

    A negative stiffness pushes the end further the more it moves, and a
    negative imaginary part puts energy into the beam instead of taking it out.
    """
    problems: list[str] = []
    for name in BeamSupports.fieldNames():
        stiffness: complex = getattr(supports, name)
        if stiffness.real < 0:
            problems.append(f"The stiffness of the {springNames[name]} cannot be negative.")
        if stiffness.imag < 0:
            problems.append(f"The damping of the {springNames[name]} cannot be negative.")
    return problems


def loadSupports() -> BeamSupports:
    """The springs last saved, with 0 (a free end) for any part missing or unreadable."""
    settings = settingsService.openSettings()
    supports = BeamSupports()
    for name in BeamSupports.fieldNames():
        parts = []
        for part in ("real", "imag"):
            value = settings.value(f"{settingsGroup}/{name}/{part}")
            try:
                parts.append(0.0 if value is None else float(value))
            except (TypeError, ValueError):
                logger.warning("Ignoring unreadable saved %s %s: %r", name, part, value)
                parts.append(0.0)
        supports = replace(supports, **{name: complex(*parts)})
    return supports


def saveSupports(supports: BeamSupports) -> None:
    for name in BeamSupports.fieldNames():
        stiffness: complex = getattr(supports, name)
        settingsService.writeValue(f"{settingsGroup}/{name}/real", stiffness.real)
        settingsService.writeValue(f"{settingsGroup}/{name}/imag", stiffness.imag)

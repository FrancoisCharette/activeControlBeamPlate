"""Checks and keeps how the beam is driven (Beam > Actuation).

Kept in the settings file under "beam/actuation/", so the excitation, the
voltage and the frequency band are there the next time the app starts.
"""

from __future__ import annotations

import logging
import math
from dataclasses import replace

from activeControlBeamPlate.models.beamActuation import BeamActuation, Excitation
from activeControlBeamPlate.models.beamGeometry import BeamGeometry
from activeControlBeamPlate.services import settingsService

logger = logging.getLogger(__name__)

settingsGroup = "beam/actuation"
numberFields = (
    "voltageAmplitude", "voltagePhase", "frequencyStart", "frequencyEnd", "frequencyStep"
)
# A band of more frequencies than this is almost certainly a mistyped step.
maximumFrequencies = 1_000_000


def frequencyCount(actuation: BeamActuation) -> int:
    """How many frequencies the band holds, both ends included; 0 if it holds none."""
    span = actuation.frequencyEnd - actuation.frequencyStart
    if actuation.frequencyStep <= 0 or span < 0:
        return 0
    # The small allowance keeps an end that is a whole number of steps away, such
    # as 3200 from 1 in steps of 1, from being lost to rounding.
    return math.floor(span / actuation.frequencyStep + 1e-9) + 1


def problemsWith(actuation: BeamActuation, geometry: BeamGeometry) -> list[str]:
    """Each way the actuation cannot be used; empty if none."""
    problems: list[str] = []
    if actuation.voltageAmplitude <= 0:
        problems.append("The voltage amplitude must be greater than zero.")
    if actuation.frequencyStep <= 0:
        problems.append("The frequency step must be greater than zero.")
    if actuation.frequencyEnd <= actuation.frequencyStart:
        problems.append("The end of the frequency band must be above its start.")
    elif frequencyCount(actuation) > maximumFrequencies:
        problems.append(
            f"The band holds {frequencyCount(actuation):,} frequencies; use a larger step "
            f"(at most {maximumFrequencies:,})."
        )
    if actuation.excitation.isSymmetric and overlapsSensor(geometry):
        problems.append(
            "A symmetric excitation puts a second actuator on the lower surface, facing the "
            f"first at x = {geometry.actuatorPosition:g} mm, where the sensor is "
            f"(x = {geometry.sensorPosition - geometry.sensorLength / 2:g} to "
            f"{geometry.sensorPosition + geometry.sensorLength / 2:g} mm). Move or shorten "
            "the sensor on the Parameters tab, or drive the beam asymmetrically."
        )
    return problems


def overlapsSensor(geometry: BeamGeometry) -> bool:
    """Whether a lower element facing the actuator would cover part of the sensor."""
    actuatorStart = geometry.actuatorPosition - geometry.actuatorLength / 2
    actuatorEnd = geometry.actuatorPosition + geometry.actuatorLength / 2
    sensorStart = geometry.sensorPosition - geometry.sensorLength / 2
    sensorEnd = geometry.sensorPosition + geometry.sensorLength / 2
    return actuatorStart < sensorEnd and sensorStart < actuatorEnd


def loadActuation() -> BeamActuation:
    """The actuation last saved, with the default for anything missing or unreadable."""
    settings = settingsService.openSettings()
    actuation = BeamActuation()
    name = settings.value(f"{settingsGroup}/excitation")
    if name is not None:
        try:
            actuation = replace(actuation, excitation=Excitation[str(name)])
        except KeyError:
            logger.warning("Ignoring unknown saved excitation: %r", name)
    for field in numberFields:
        value = settings.value(f"{settingsGroup}/{field}")
        if value is None:
            continue
        try:
            actuation = replace(actuation, **{field: float(value)})
        except (TypeError, ValueError):
            logger.warning("Ignoring unreadable saved %s: %r", field, value)
    return actuation


def saveActuation(actuation: BeamActuation) -> None:
    values: dict[str, object] = {f"{settingsGroup}/excitation": actuation.excitation.name}
    values.update(
        {f"{settingsGroup}/{field}": getattr(actuation, field) for field in numberFields}
    )
    settingsService.writeValues(values)

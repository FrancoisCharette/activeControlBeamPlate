"""Tests for the beam materials of Table 2.2: the checks and what is kept."""

from __future__ import annotations

from dataclasses import replace

from activeControlBeamPlate.models.beamMaterials import BeamMaterials
from activeControlBeamPlate.services import beamMaterialsService, settingsService


def testTheDefaultsAreTable22() -> None:
    assert BeamMaterials() == BeamMaterials(
        beamDensity=2726.0,
        beamYoungsModulus=71e9 + 35.5e7j,
        actuatorDensity=7614.0,
        actuatorYoungsModulus=63e9 + 0j,
        actuatorDzx=190e-12,
        actuatorEzx=12.0,
        sensorDensity=3400.0,
        sensorYoungsModulus=2e9 + 0j,
        sensorPermittivity=106e-12,
        sensorDzx=23e-12,
        sensorEzx=0.046,
    )


def testTable22sEzxIsCloseToDzxTimesY() -> None:
    """Equation 2.24, as the note on the page says."""
    materials = BeamMaterials()

    for part in ("actuator", "sensor"):
        dzx = getattr(materials, f"{part}Dzx")
        modulus = getattr(materials, f"{part}YoungsModulus").real
        assert abs(getattr(materials, f"{part}Ezx") - dzx * modulus) < 0.05


def testTable22HasNoProblems() -> None:
    assert beamMaterialsService.problemsWith(BeamMaterials()) == []


def testImpossibleMaterialsAreNamed() -> None:
    materials = replace(
        BeamMaterials(),
        beamDensity=0.0,
        actuatorYoungsModulus=-1.0 + 0j,
        sensorYoungsModulus=2e9 - 5j,
        sensorPermittivity=0.0,
    )

    assert beamMaterialsService.problemsWith(materials) == [
        "The beam density must be greater than zero.",
        "The actuator Young's modulus must be greater than zero.",
        "The damping of the sensor Young's modulus cannot be negative.",
        "The sensor permittivity must be greater than zero.",
    ]


def testAPiezoelectricConstantMayBeNegative() -> None:
    """Its sign depends on how the element is poled and wired."""
    materials = replace(BeamMaterials(), sensorDzx=-23e-12, sensorEzx=-0.046)

    assert beamMaterialsService.problemsWith(materials) == []


def testNothingSavedMeansTable22() -> None:
    assert beamMaterialsService.loadMaterials() == BeamMaterials()


def testTheMaterialsComeBackAsSaved() -> None:
    materials = replace(
        BeamMaterials(), beamYoungsModulus=70e9 + 1e9j, sensorPermittivity=110e-12,
        actuatorDzx=-171e-12,
    )

    beamMaterialsService.saveMaterials(materials)

    assert beamMaterialsService.loadMaterials() == materials


def testAnUnreadableSavedValueFallsBackToTable22ForThatValueOnly() -> None:
    beamMaterialsService.saveMaterials(replace(BeamMaterials(), sensorDensity=1780.0))
    settingsService.writeValue(f"{beamMaterialsService.settingsGroup}/beamDensity", "heavy")

    materials = beamMaterialsService.loadMaterials()

    assert materials.beamDensity == 2726.0
    assert materials.sensorDensity == 1780.0

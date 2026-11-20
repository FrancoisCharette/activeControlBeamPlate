"""Tests for the plate configuration of Figure 5.1 and Table 5.1: the checks and what is kept."""

from __future__ import annotations

from dataclasses import replace

from activeControlBeamPlate.models.plateConfiguration import (
    EdgeSupport,
    PlateActuator,
    PlateConfiguration,
    PlateProperties,
    PlateSupports,
)
from activeControlBeamPlate.services import plateConfigurationService, settingsService


def withPrimary(**changes: float) -> PlateConfiguration:
    configuration = PlateConfiguration()
    return replace(configuration, primaryActuator=replace(configuration.primaryActuator, **changes))


def testTheDefaultsAreTable51() -> None:
    configuration = PlateConfiguration()

    assert configuration.plate == PlateProperties(
        length=480.0, width=420.0, thickness=3.22, density=2700.0,
        youngsModulus=66.5e9 + 33e7j, poissonRatio=0.33,
    )
    common = dict(length=38.1, width=31.8, thickness=0.254, density=7750.0,
                  youngsModulus=63e9 + 0j, poissonRatio=0.33, ezx=14.0, dzx=210e-12)
    assert configuration.primaryActuator == PlateActuator(**common, positionX=-69.0,
                                                          positionY=86.1)
    assert configuration.secondaryActuator == PlateActuator(**common, positionX=-39.5,
                                                            positionY=-35.6)


def testTheEdgesStartFreeBecauseTheThesisGivesNoValues() -> None:
    assert PlateConfiguration().supports == PlateSupports()
    assert EdgeSupport() == EdgeSupport(transverse=0j, rotational=0j)


def testTable51DescribesAPlateThatCanBeBuilt() -> None:
    assert plateConfigurationService.problemsWith(PlateConfiguration()) == []


def testAnActuatorPastAnEdgeIsNamedWithWhereItIs() -> None:
    problems = plateConfigurationService.problemsWith(withPrimary(positionY=200.0))

    assert problems == [
        "The primary actuator runs past the edge of the plate in y: it spans y = 184.1 to "
        "215.9 mm, and the plate y = -210 to 210 mm."
    ]


def testAnActuatorMayTouchAnEdge() -> None:
    assert plateConfigurationService.problemsWith(withPrimary(positionX=240.0 - 38.1 / 2)) == []


def testOverlappingActuatorsAreCaught() -> None:
    configuration = withPrimary(positionX=-39.5, positionY=-35.6 + 10.0)

    assert plateConfigurationService.problemsWith(configuration) == [
        "The primary and secondary actuators overlap; they cannot share the plate's surface."
    ]


def testActuatorsSideBySideDoNotOverlap() -> None:
    assert plateConfigurationService.problemsWith(withPrimary(positionX=-39.5 + 38.1,
                                                              positionY=-35.6)) == []


def testImpossibleMaterialsAreCaught() -> None:
    configuration = PlateConfiguration()
    configuration = replace(
        configuration,
        plate=replace(configuration.plate, thickness=0.0, poissonRatio=0.6,
                      youngsModulus=66.5e9 - 1j),
    )

    assert plateConfigurationService.problemsWith(configuration) == [
        "The plate thickness must be greater than zero.",
        "The damping of the plate Young's modulus cannot be negative.",
        "The plate Poisson's ratio must be between -1 and 0.5.",
    ]


def testANegativeEdgeSpringIsNamedWithItsEdge() -> None:
    configuration = replace(
        PlateConfiguration(),
        supports=replace(PlateSupports(), edgeYPositive=EdgeSupport(rotational=-2.0)),
    )

    assert plateConfigurationService.problemsWith(configuration) == [
        "The rotational stiffness of the edge y = +L_y/2 cannot be negative."
    ]


def testNothingSavedMeansTable51() -> None:
    assert plateConfigurationService.loadConfiguration() == PlateConfiguration()


def testTheConfigurationComesBackAsSaved() -> None:
    configuration = replace(
        withPrimary(positionX=10.0, dzx=-171e-12, youngsModulus=60e9 + 1e8j),
        supports=replace(PlateSupports(), edgeXNegative=EdgeSupport(1e12 + 5e9j, 3.5)),
    )

    plateConfigurationService.saveConfiguration(configuration)

    assert plateConfigurationService.loadConfiguration() == configuration


def testAnUnreadableSavedValueFallsBackToTable51ForThatValueOnly() -> None:
    plateConfigurationService.saveConfiguration(withPrimary(positionX=10.0))
    settingsService.writeValue("plate/plate/length", "long")

    configuration = plateConfigurationService.loadConfiguration()

    assert configuration.plate.length == 480.0
    assert configuration.primaryActuator.positionX == 10.0

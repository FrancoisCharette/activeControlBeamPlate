"""Tests for the number box used for stiffnesses."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QValidator

from activeControlBeamPlate.ui.widgets.scientificSpinBox import ScientificSpinBox


@pytest.fixture
def box(qtbot) -> ScientificSpinBox:
    spinBox = ScientificSpinBox()
    qtbot.addWidget(spinBox)
    return spinBox


def testLargeAndSmallValuesAreWrittenShort(box) -> None:
    assert box.textFromValue(1e12) == "1e+12"
    assert box.textFromValue(2.5e6) == "2.5e+06"
    assert box.textFromValue(350.0) == "350"
    assert box.textFromValue(0.0) == "0"


def testItKeepsTheValueExactly(box) -> None:
    """A plain spin box rounds to its decimals; 1.234567e-7 must survive."""
    box.setValue(1.234567e-7)

    assert box.value() == 1.234567e-7


@pytest.mark.parametrize("text, value", [("1e9", 1e9), ("2.5E6", 2.5e6), ("0.001", 0.001)])
def testTypedNumbersAreRead(box, text: str, value: float) -> None:
    assert box.validate(text, len(text))[0] == QValidator.State.Acceptable
    assert box.valueFromText(text) == value


@pytest.mark.parametrize("text", ["", "1e", "2.5E-", "."])
def testANumberHalfTypedIsAllowedToContinue(box, text: str) -> None:
    assert box.validate(text, len(text))[0] == QValidator.State.Intermediate


@pytest.mark.parametrize("text", ["abc", "1e9x", "1,5"])
def testWhatCannotBecomeANumberIsRefused(box, text: str) -> None:
    assert box.validate(text, len(text))[0] == QValidator.State.Invalid


def testANumberOutsideTheRangeIsNotAccepted(box) -> None:
    assert box.validate("-5", 2)[0] == QValidator.State.Intermediate
    assert box.validate("1e20", 4)[0] == QValidator.State.Intermediate


def testTheArrowsStepByFactorsOfTen(box) -> None:
    box.stepBy(1)
    assert box.value() == 1.0  # from 0, the first step up

    box.stepBy(3)
    assert box.value() == pytest.approx(1000.0)

    box.stepBy(-1)
    assert box.value() == pytest.approx(100.0)


def testStepsStopAtTheMaximum(box) -> None:
    box.setValue(1e14)

    box.stepBy(5)

    assert box.value() == box.maximum()


def testTheBoxIsWideEnoughForAnyValueItShows(box) -> None:
    """Qt sizes a spin box for its minimum and maximum, here "0" and "1e+15"; in a narrow
    column 1.00081e+06 lost its exponent and read as 1.00081."""
    metrics = box.fontMetrics()

    assert box.minimumSizeHint().width() > metrics.horizontalAdvance("-8.88888e-888")
    assert box.sizeHint().width() >= box.minimumSizeHint().width()

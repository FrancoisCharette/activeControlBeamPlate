"""A number box for values that span many orders of magnitude, such as stiffnesses.

A plain QDoubleSpinBox writes 1e9 as 1000000000.00 and has a fixed step, so a
stiffness that may be 0, 50 or 1e12 is hard to read and to set. This one
shows six significant digits (1e+09, 2.5e+06, 350), accepts anything Python
reads as a number (1e9, 2.5E6, 0.001), and steps by factors of ten with the
arrows or the keyboard, from 0 to 1 on the first step up.
"""

from __future__ import annotations

import math
import re

from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QDoubleSpinBox, QWidget

significantDigits = 6
# What is on the way to a number while it is typed: "", "-", "1e", "2.5E-".
unfinished = re.compile(r"[+-]?(\d*\.?\d*([eE][+-]?)?)?")


class ScientificSpinBox(QDoubleSpinBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Qt rounds every value to this many decimals; this keeps them all.
        self.setDecimals(323)
        self.setRange(0.0, 1e15)

    def stripAffixes(self, text: str) -> str:
        body = text
        if self.prefix() and body.startswith(self.prefix()):
            body = body[len(self.prefix()):]
        if self.suffix() and body.endswith(self.suffix()):
            body = body[: -len(self.suffix())]
        return body.strip()

    def textFromValue(self, value: float) -> str:
        return f"{value:.{significantDigits}g}"

    def valueFromText(self, text: str) -> float:
        try:
            return float(self.stripAffixes(text))
        except ValueError:
            return self.value()

    def validate(self, text: str, position: int) -> tuple[QValidator.State, str, int]:
        body = self.stripAffixes(text)
        try:
            value = float(body)
        except ValueError:
            state = (QValidator.State.Intermediate if unfinished.fullmatch(body)
                     else QValidator.State.Invalid)
            return state, text, position
        if math.isfinite(value) and self.minimum() <= value <= self.maximum():
            return QValidator.State.Acceptable, text, position
        return QValidator.State.Intermediate, text, position

    def fixup(self, text: str) -> str:
        # Leaving an unfinished entry puts back the value it had.
        return self.textFromValue(self.value())

    def stepBy(self, steps: int) -> None:
        value = self.value()
        if value == 0:
            self.setValue(1.0 if steps > 0 else 0.0)
        else:
            self.setValue(min(value * 10.0**steps, self.maximum()))

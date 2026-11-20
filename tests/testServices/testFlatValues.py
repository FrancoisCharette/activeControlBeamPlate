"""Tests for writing nested dataclasses as flat keys and reading them back."""

from __future__ import annotations

from dataclasses import dataclass, field

from activeControlBeamPlate.services.flatValues import flatten, rebuild


@dataclass(frozen=True)
class Inner:
    stiffness: complex = 1 + 2j
    length: float = 3.0


@dataclass(frozen=True)
class Outer:
    inner: Inner = field(default_factory=Inner)
    ratio: float = 0.5


def testEveryNumberGetsAPathAndAComplexOneGetsTwo() -> None:
    assert flatten(Outer()) == {
        "inner/stiffness/real": 1.0,
        "inner/stiffness/imag": 2.0,
        "inner/length": 3.0,
        "ratio": 0.5,
    }


def testRebuildingFromTheFlatValuesGivesTheSameThing() -> None:
    value = Outer(inner=Inner(stiffness=5 - 0.5j, length=7.0), ratio=0.25)
    flat = flatten(value)

    assert rebuild(Outer(), flat.get) == value


def testWhatTheReaderDoesNotKnowKeepsItsDefault() -> None:
    """Including half of a complex number."""
    known = {"inner/stiffness/imag": 9.0, "ratio": 0.75}

    assert rebuild(Outer(), known.get) == Outer(inner=Inner(stiffness=1 + 9j), ratio=0.75)


def testAPrefixNamesTheWholeTree() -> None:
    assert "plate/ratio" in flatten(Outer(), "plate")


def testAPlainNumberInAComplexFieldIsKeptAsAComplexOne() -> None:
    """Otherwise it is written under a key the reader never asks for, and lost."""
    value = Outer(inner=Inner(stiffness=3.5))

    flat = flatten(value)

    assert flat["inner/stiffness/real"] == 3.5 and flat["inner/stiffness/imag"] == 0.0
    assert rebuild(Outer(), flat.get) == value

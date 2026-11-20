"""Nested dataclasses of numbers, written out as flat "a/b/c" keys and read back.

A configuration such as PlateConfiguration nests dataclasses several deep and
holds complex numbers. Both the settings file and the inputs on a page deal
in single numbers under a name, so the two meet here:

- `flatten` lists every number under its path; a complex number becomes two,
  "<path>/real" and "<path>/imag".
- `rebuild` makes the dataclass back from a reader that answers a path with a
  number, or None for "not known", in which case the default stands.

Plain Python, no Qt, so the same paths name a setting and an input.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import Field, fields, is_dataclass, replace
from typing import Any

Reader = Callable[[str], float | None]


def join(prefix: str, name: str) -> str:
    return f"{prefix}/{name}" if prefix else name


def isComplexField(item: Field) -> bool:
    # Annotations are strings under `from __future__ import annotations`.
    return item.type in ("complex", complex)


def flatten(value: Any, prefix: str = "") -> dict[str, float]:
    if is_dataclass(value):
        flat: dict[str, float] = {}
        for item in fields(value):
            member = getattr(value, item.name)
            # A complex field given a plain number, EdgeSupport(rotational=3.5) say, is
            # still a complex number: it is kept under the same two keys as any other.
            if isComplexField(item):
                member = complex(member)
            flat.update(flatten(member, join(prefix, item.name)))
        return flat
    if isinstance(value, complex):
        return {join(prefix, "real"): value.real, join(prefix, "imag"): value.imag}
    return {prefix: float(value)}


def rebuild[T](default: T, read: Reader, prefix: str = "") -> T:
    """`default` with every number `read` knows put in its place."""
    if is_dataclass(default):
        return replace(default, **{
            item.name: rebuild(getattr(default, item.name), read, join(prefix, item.name))
            for item in fields(default)
        })
    if isinstance(default, complex):
        real, imag = read(join(prefix, "real")), read(join(prefix, "imag"))
        return complex(
            default.real if real is None else real, default.imag if imag is None else imag
        )
    value = read(prefix)
    return default if value is None else value

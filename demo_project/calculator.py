"""Tiny demo module with a deliberate bug for the diagnosis workflow."""


def add(a: int, b: int) -> int:
    return a + b


def subtract(a: int, b: int) -> int:
    # BUG: should be a - b
    return a + b


def multiply(a: int, b: int) -> int:
    return a * b

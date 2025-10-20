import pytest
from src.calc import sum


def test_sum_positive_numbers():
    assert sum(2, 3) == 5


def test_sum_negative_numbers():
    assert sum(-1, -1) == -2


def test_sum_mixed_numbers():
    assert sum(5, -3) == 2


def test_sum_zero():
    assert sum(0, 0) == 0
    assert sum(5, 0) == 5


def test_sum_floats():
    assert sum(1.5, 2.5) == 4.0

import pytest
from src.hello import say_hello


def test_say_hello():
    assert say_hello() == 'hello'


def test_say_hello_negative():
    assert say_hello() != 'hi'

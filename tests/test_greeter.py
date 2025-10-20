import pytest
from src.greeter import greet
import subprocess


def test_greet_simple():
    assert greet('Ana') == 'Hello, Ana!'


def test_greet_different_names():
    assert greet('John') == 'Hello, John!'
    assert greet('Maria') == 'Hello, Maria!'
    assert greet('Zoe') == 'Hello, Zoe!'


def test_greet_empty_string():
    assert greet('') == 'Hello, !'


def test_cli_acceptance():
    result = subprocess.run(['python', '-m', 'src.greeter', '--name', 'Ana'], capture_output=True, text=True)
    assert result.stdout.strip() == 'Hello, Ana!'
    assert result.returncode == 0


def test_import_greet():
    try:
        from src.greeter import greet
    except ImportError:
        pytest.fail('Failed to import greet from src.greeter')


def test_main_execution():
    result = subprocess.run(['python', '-m', 'src.greeter', '--name', 'Ana'], capture_output=True, text=True)
    assert result.stdout.strip() == 'Hello, Ana!'
    assert result.returncode == 0

import subprocess
import pytest
from src.greeter import greet

def test_greet_with_name():
    assert greet('Ana') == 'Hello, Ana!'

def test_greet_various_names():
    names = ['Ana', 'John', 'Maria', 'Zoe']
    for name in names:
        assert greet(name) == f'Hello, {name}!'

def test_cli_greet():
    result = subprocess.run(['python', '-m', 'src.greeter', '--name', 'Ana'], capture_output=True, text=True)
    assert result.stdout.strip() == 'Hello, Ana!'
    assert result.returncode == 0

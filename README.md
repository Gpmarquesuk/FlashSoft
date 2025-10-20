# Project

A Python project with utilities and CLI tools.

## Features

### Greeter

A simple greeting utility that can be used as a module or CLI tool.

**Usage as module:**

```python
from src.greeter import greet

print(greet("Ana"))  # Output: Hello, Ana!
```

**Usage as CLI:**

```bash
python -m src.greeter --name Ana
# Output: Hello, Ana!
```

## Testing

Run tests with pytest:

```bash
pytest
```

## Development

Code follows PEP 8 style guidelines.

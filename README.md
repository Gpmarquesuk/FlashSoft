# Project

A Python project with utilities and CLI tools.

## Features

- **Greeter**: Simple greeting utility with CLI support
- **Hello**: Basic hello world module

## Usage

### Greeter CLI

Run the greeter from command line:

```bash
python -m src.greeter --name Ana
```

Output:
```
Hello, Ana!
```

### Greeter in Code

```python
from src.greeter import greet

print(greet("Ana"))  # Hello, Ana!
```

## Testing

Run tests with pytest:

```bash
pytest
```

## Development

Code follows PEP8 style guidelines.

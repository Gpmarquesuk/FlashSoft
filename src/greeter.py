"""Greeter utility module."""


def greet(name):
    """Return a greeting message for the given name.
    
    Args:
        name: The name to greet.
        
    Returns:
        A greeting string.
    """
    return f"Hello, {name}!"


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Greet someone")
    parser.add_argument("--name", required=True, help="Name to greet")
    args = parser.parse_args()
    
    print(greet(args.name))

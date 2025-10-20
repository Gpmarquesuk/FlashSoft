"""Calculator utility module."""
import argparse


def sum(a, b):
    """Return the sum of a and b."""
    return a + b


def main():
    """CLI entry point for calculator."""
    parser = argparse.ArgumentParser(description='Calculator utility')
    parser.add_argument('--a', type=float, required=True, help='First number')
    parser.add_argument('--b', type=float, required=True, help='Second number')
    args = parser.parse_args()
    
    result = sum(args.a, args.b)
    print(int(result) if result == int(result) else result)


if __name__ == '__main__':
    main()

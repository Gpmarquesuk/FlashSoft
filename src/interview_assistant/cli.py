import argparse

from .assistant import run_cli


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the interview assistant CLI")
    parser.add_argument("--resume", required=True)
    parser.add_argument("--jd", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--output-dir", default="artifacts")
    parser.add_argument("--logs-dir", default="logs")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_cli(args.resume, args.jd, args.question, args.output_dir, args.logs_dir)


if __name__ == "__main__":
    main()

from src.interview_assistant.cli import build_parser


def test_cli_parser_has_expected_arguments():
    parser = build_parser()
    args = parser.parse_args(
        [
            "--resume",
            "resume.json",
            "--jd",
            "jd.md",
            "--question",
            "Tell me about yourself",
        ]
    )
    assert args.resume.endswith("resume.json")
    assert args.question

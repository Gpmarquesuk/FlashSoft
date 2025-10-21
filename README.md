# Realtime Interview Assistant

## Description
During online interviews, given a question, combine the question with the candidate resume and the job description to synthesize a concise, high-quality answer and display it on screen.

## Usage
```bash
python -m src.interview_assistant --resume data/resume.json --jd data/jd.md --question "Question"
```

## Artifacts
- `artifacts/last_answer.json`: JSON file containing the final answer, talking points, and sources.
- `artifacts/overlay.html`: HTML file containing the final answer, talking points, and sources.
- `logs/agent_chat/<run_id>.md`: Markdown file containing the chat log for the run.

## Tests
```bash
pytest
```

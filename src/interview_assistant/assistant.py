import json
import os
from dataclasses import dataclass
from pathlib import Path
import uuid


@dataclass
class Answer:
    final_answer: str
    talking_points: list[str]
    sources: list[str]


class InterviewAssistant:
    def __init__(self, resume_path, jd_path, output_dir=Path('artifacts'), logs_dir=Path('logs')):
        self.resume_path = Path(resume_path)
        self.jd_path = Path(jd_path)
        self.output_dir = Path(output_dir)
        self.logs_dir = Path(logs_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.logs_dir / 'agent_chat').mkdir(parents=True, exist_ok=True)

    def _load_resume(self) -> dict:
        return json.loads(self.resume_path.read_text(encoding='utf-8'))

    def _load_jd(self) -> str:
        return self.jd_path.read_text(encoding='utf-8')

    def build_answer(self, question: str) -> Answer:
        resume = self._load_resume()
        jd = self._load_jd()
        strengths = [resume.get('summary', ''), *resume.get('achievements', [])]
        talking_points = [p for p in strengths if p][:3]
        if not talking_points:
            talking_points = ["Highlight adaptability", "Relacionar experiencia com a vaga"]
        sources = ["resume", "job_description"]
        final_answer = f"{resume.get('name', 'Candidate')} pode ajudar em '{question}' destacando: " + ", ".join(talking_points)
        if len(final_answer.split()) > 120:
            final_answer = " ".join(final_answer.split()[:120]) + "..."
        return Answer(final_answer=final_answer, talking_points=talking_points, sources=sources)

    def _artifact_paths(self):
        json_path = self.output_dir / 'last_answer.json'
        overlay_path = self.output_dir / 'overlay.html'
        log_path = self.logs_dir / 'agent_chat' / f"{uuid.uuid4().hex}.md"
        return json_path, overlay_path, log_path

    def _write_artifacts(self, question: str, answer: Answer):
        json_path, overlay_path, log_path = self._artifact_paths()
        json_path.write_text(
            json.dumps(
                {
                    'question': question,
                    'final_answer': answer.final_answer,
                    'talking_points': answer.talking_points,
                    'sources': answer.sources,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding='utf-8',
        )
        points_html = "".join(f"<li>{tp}</li>" for tp in answer.talking_points)
        sources_html = "".join(f"<li>{src}</li>" for src in answer.sources)
        overlay_html = (
            f"<html><body><h1>Final Answer</h1><p>{answer.final_answer}</p>"
            f"<h2>Talking Points</h2><ul>{points_html}</ul>"
            f"<h2>Sources</h2><ul>{sources_html}</ul></body></html>"
        )
        overlay_path.write_text(overlay_html, encoding='utf-8')
        log_path.write_text(
            f"# Chat Log\n\nPergunta: {question}\n\nResposta: {answer.final_answer}",
            encoding='utf-8',
        )

    def run(self, question: str) -> Answer:
        answer = self.build_answer(question)
        self._write_artifacts(question, answer)
        return answer


Assistant = InterviewAssistant

def run_cli(resume: str, jd: str, question: str, output_dir: str = 'artifacts', logs_dir: str = 'logs') -> None:
    assistant = InterviewAssistant(resume, jd, output_dir=output_dir, logs_dir=logs_dir)
    assistant.run(question)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', required=True)
    parser.add_argument('--jd', required=True)
    parser.add_argument('--question', required=True)
    parser.add_argument('--output-dir', default='artifacts')
    parser.add_argument('--logs-dir', default='logs')
    args = parser.parse_args()
    run_cli(args.resume, args.jd, args.question, args.output_dir, args.logs_dir)

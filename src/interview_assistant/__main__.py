import argparse
import json
import os
from datetime import datetime
import uuid

from .retriever import Retriever
from .generator import generate_answer
from .overlay import show_overlay, generate_html


def main():
    parser = argparse.ArgumentParser(description='Realtime Interview Assistant')
    parser.add_argument('--resume', required=True, help='Path to resume JSON')
    parser.add_argument('--jd', required=True, help='Path to job description MD')
    parser.add_argument('--question', required=True, help='Interview question')
    parser.add_argument('--mode', choices=['topmost_window', 'overlay_html'], default='topmost_window', help='Display mode')
    args = parser.parse_args()

    run_id = str(uuid.uuid4())
    log_dir = 'logs/agent_chat'
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f'{run_id}.md')

    # Load documents
    with open(args.resume, 'r') as f:
        resume = json.load(f)
    with open(args.jd, 'r') as f:
        jd = f.read()

    # Retrieval
    retriever = Retriever()
    retriever.add_document('resume', json.dumps(resume, indent=2))
    retriever.add_document('jd', jd)
    chunks = retriever.retrieve(args.question, top_k=5)

    # Generate answer
    answer = generate_answer(args.question, resume, jd, chunks, log_path)

    # Output markdown sections
    print(answer)

    # Save artifact JSON
    os.makedirs('artifacts', exist_ok=True)
    artifact_path = 'artifacts/last_answer.json'
    with open(artifact_path, 'w') as f:
        json.dump({'answer': answer, 'run_id': run_id, 'question': args.question}, f, indent=2)

    # Overlay
    overlay_path = 'artifacts/overlay.html'
    try:
        if args.mode == 'topmost_window':
            show_overlay(answer)
        else:
            html = generate_html(answer)
            with open(overlay_path, 'w') as f:
                f.write(html)
            import webbrowser
            webbrowser.open(overlay_path)
    except Exception as e:
        print(f'Overlay failed ({args.mode}): {e}. Falling back to HTML.')
        html = generate_html(answer)
        with open(overlay_path, 'w') as f:
            f.write(html)


if __name__ == '__main__':
    main()
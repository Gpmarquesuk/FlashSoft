import argparse
import json
from pathlib import Path
from datetime import datetime
from src.interview.assistant import InterviewAssistant

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resume', required=True)
    parser.add_argument('--jd', required=True)
    parser.add_argument('--question', required=True)
    args = parser.parse_args()

    assistant = InterviewAssistant(args.resume, args.jd)
    result = assistant.generate_answer(args.question)
    
    output_dir = Path('artifacts')
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON
    (output_dir / 'last_answer.json').write_text(json.dumps(result))
    
    # Generate markdown output
    md_content = f"## Final answer\n{result['Final answer']}\n\n" \
                 f"## Talking points\n- " + '\n- '.join(result['Talking points']) + '\n\n' \
                 f"## Sources\n- " + '\n- '.join(result['Sources'])
    print(md_content)
    
    # Logging
    log_dir = Path('logs/agent_chat')
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f'{datetime.now().isoformat()}.md').write_text(md_content)

if __name__ == '__main__':
    main()
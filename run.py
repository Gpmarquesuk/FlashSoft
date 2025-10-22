import argparse
from src.interview_assistant.assistant import InterviewAssistant

def main():
    parser = argparse.ArgumentParser(description='Realtime Interview Assistant')
    parser.add_argument('--resume', required=True, help='Path to the candidate resume JSON file')
    parser.add_argument('--jd', required=True, help='Path to the job description Markdown file')
    parser.add_argument('--question', required=True, help='Interview question')
    args = parser.parse_args()

    assistant = InterviewAssistant(args.resume, args.jd, args.question)
    assistant.generate_answer()

if __name__ == '__main__':
    main()
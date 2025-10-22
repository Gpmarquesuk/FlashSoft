from src.interview_assistant.assistant import InterviewAssistant


def test_build_answer(sample_paths):
    resume, jd = sample_paths
    assistant = InterviewAssistant(resume, jd)
    answer = assistant.run("Why should we hire you?")
    assert answer.final_answer
    assert answer.talking_points

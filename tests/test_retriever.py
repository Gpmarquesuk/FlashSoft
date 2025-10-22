from src.interview_assistant.assistant import InterviewAssistant


def test_retrieval_basic(sample_paths):
    resume, jd = sample_paths
    assistant = InterviewAssistant(resume, jd)
    answer = assistant.run("Why should we hire you?")
    assert set(answer.sources) == {"resume", "job_description"}

import json

# Assuming llm_client is available and configured for OpenRouter
from llm_client import LLMClient


def generate_answer(question, resume, jd, chunks, log_path):
    client = LLMClient()

    # Prepare context
    resume_str = json.dumps(resume)
    jd_summary = jd[:500] + '...' if len(jd) > 500 else jd
    chunks_text = '\n'.join([f"- {c['text'][:100]}... (score: {c['score']:.2f})" for c in chunks])

    prompt = f"""You are an interview assistant. Synthesize a concise, high-quality answer to the question based on the candidate's resume, job description, and relevant retrieved chunks.

Resume: {resume_str}

Job Description: {jd_summary}

Relevant Chunks:
{chunks_text}

Question: {question}

Output in Markdown format with these exact sections:
# Final Answer
[A concise answer, maximum 120 words. Be professional and tailored to the job.]

# Talking Points
- Bullet point 1
- Bullet point 2
- etc.

# Sources
- List relevant sources (e.g., Resume: experience section, JD: requirements)"""

    with open(log_path, 'a') as f:
        f.write(f"## Prompt:\n{prompt[:1000]}...\n\n")

    response = client.generate(prompt)

    with open(log_path, 'a') as f:
        f.write(f"## Response:\n{response}\n\n---\n")

    return response
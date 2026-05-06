from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- SUMMARIZATION ----------------
def summarize_text(text):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Summarize this:\n{text}"}]
    )
    return res.choices[0].message.content


# ---------------- QA ----------------
def answer_question(question, context):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion:\n{question}"
        }]
    )
    return res.choices[0].message.content


# ---------------- QUIZ ----------------
def generate_quiz(text):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Generate 3 MCQs with options and answers from:\n{text}"
        }]
    )
    return res.choices[0].message.content


# ---------------- DIAGRAM ----------------
def generate_diagram(text):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Break this into steps:\n{text}"
        }]
    )

    steps_text = res.choices[0].message.content
    steps = [s.strip() for s in steps_text.split("\n") if s.strip()]

    if len(steps) < 2:
        return """graph TD
A[Start] --> B[Process]
B --> C[End]
"""

    mermaid = "graph TD\n"

    for i in range(len(steps)-1):
        mermaid += f"S{i}[{steps[i]}] --> S{i+1}[{steps[i+1]}]\n"

    return mermaid
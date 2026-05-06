from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



# 2. Imports
# ------------------------------------------------------------
import os
import faiss
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import textwrap

import networkx as nx
import matplotlib.pyplot as plt
import textwrap

# wrap text
def wrap_label(text, width=12):
    return "\n".join(textwrap.wrap(text, width))

def draw_graph_from_mermaid(mermaid_code):
    G = nx.DiGraph()
    id_to_label = {}
    #  clean function (INSIDE main function)
    def clean(node):
        node = node.strip()

       # Case 1: A["Text"]
        if "[" in node and "]" in node:
            node_id = node[:node.find("[")].strip()
            label = node[node.find("[")+1 : node.rfind("]")]
            label = label.strip('"')

            id_to_label[node_id] = wrap_label(label)
            return wrap_label(label)

    # Case 2: only A, B, C
        if node in id_to_label:
            return id_to_label[node]

        return node

    lines = mermaid_code.split("\n")

    #  build graph
    for line in lines:
        if "-->" in line:
            left, right = line.split("-->")
            G.add_edge(clean(left), clean(right))

    #  layout decision
    edge_lines = [l for l in lines if "-->" in l]

    if len(edge_lines) <= 6:
        # linear layout
        pos = {}
        for i, node in enumerate(G.nodes()):
            pos[node] = (i * 3, 0)
    else:
        # network layout
        pos = nx.spring_layout(G)

    #  draw graph
    plt.figure(figsize=(18,4))
    nx.draw(G, pos,
            with_labels=True,
            node_size=4000,
            font_size=9,
            arrows=True)

    plt.show()

import re

def clean_mermaid_output(text_output):
    text_output = text_output.replace("```", "")

    # Extract only first graph
    match = re.search(r"(graph TD[\s\S]*?)(?:graph TD|$)", text_output)
    if match:
        text_output = match.group(1)

    # Fix formatting
    lines = text_output.split("\n")
    clean_lines = []

    for line in lines:
        line = line.strip()

        if line.startswith("graph TD"):
            clean_lines.append("graph TD")

        elif "-->" in line:
            parts = line.split("-->")
            if len(parts) == 2:
                clean_lines.append(parts[0].strip() + " --> " + parts[1].strip())

    return "\n".join(clean_lines)

def ask(self, question):

    context = self.get_context(question)
    q = question.lower()

    if len(question.split()) <= 3:
        style = "short"

    elif any(word in q for word in ["define", "what is", "meaning"]):
        style = "short"

    elif any(word in q for word in ["explain", "describe", "why", "how"]):
        style = "detailed"

    elif any(word in q for word in ["difference", "compare", "advantages", "applications"]):
        style = "detailed"

    else:
        style = "medium"
    prompt = f"""
You are an intelligent academic assistant.

Answer style: {style}

Instructions based on style:
- short → 2-4 lines
- medium → 1-2 paragraphs
- detailed → structured answer with:
    • Definition
    • Explanation
    • Key Concepts
    • Example
    • Summary

General Instructions:
- Answer like a university professor teaching a student
- Use ONLY the provided context
- Do not just summarize — explain in your own words
- Make explanations clear and intuitive
- Avoid repetition
- Highlight key ideas
- Keep answers relevant to the question

Context:
{context}

Question:
{question}

Answer:
"""

    res = self.client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content
def generate_diagram(text):
    prompt = f"""
Create a clean and academic flowchart for the concept below.

Concept:
{text}

Instructions:
- Break into clear stages or steps
- Each node should be a meaningful concept (like First Generation, Transistors, etc.)
- Flow should be linear (top to bottom)
- Avoid cycles or loops
- Keep labels short and clear

Rules:
- Use graph TD
- Max 5–6 nodes
- No explanation text

Output:
graph TD
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.3
        )
    except Exception as e:
        print("OPENAI ERROR:", e)
        return """graph TD
A[Start] --> B[Process]
B --> C[End]
"""

    #  CLEAN OUTPUT
    text_output = response.choices[0].message.content

    #  remove code blocks
    text_output = text_output.replace("```", "")

    #  cut only diagram part
    if "graph TD" in text_output:
        text_output = text_output[text_output.index("graph TD"):]

    #  remove explanation after diagram
    lines = text_output.split("\n")
    clean_lines = []

    for line in lines:
        if "flowchart" in line.lower() or "this" in line.lower():
            break
        clean_lines.append(line)

    text_output = "\n".join(clean_lines)
    cleaned = clean_mermaid_output(text_output)

    #  fallback if diagram is empty/broken
    if cleaned.strip() == "graph TD":
        return """graph TD
    A[Start] --> B[Process]
    B --> C[End]
    """

    return cleaned

# 3. Load Models (Option A)
# ------------------------------------------------------------
print("Loading models...")

EMBED_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

QA_MODEL_NAME = "google/flan-t5-base"

print("Models loaded successfully!")

# 4. PDF / Text Loading
# ------------------------------------------------------------
def read_pdf(path):
    reader = PdfReader(path)
    pages = []
    empty_pages = 0 

    for i, p in enumerate(reader.pages):
        text = p.extract_text()

        if text and text.strip():
            pages.append((i+1, text))
        else:
            empty_pages += 1

    #  Case 1: Completely empty
    if len(pages) == 0:
        return None, "EMPTY_OR_IMAGE_PDF"

    return pages, None

# 5. Chunking
# ------------------------------------------------------------
def chunk_text(pages, chapters, chunk_size=800):
    chunks = []
    current_chapter = "Unknown"

    for page_num, text in pages:

        # detect chapter for page
        if page_num in chapters:
            current_chapter = chapters[page_num]

        words = text.split()

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])

            chunks.append({
                "page": page_num,
                "text": chunk,
                "chapter": current_chapter   
            })

    return chunks

  # CHAPTER DETECTION (simple)
# ------------------------------------------------------------
import re

def detect_chapters(pages):
    chapters = {}

    for page_num, text in pages:
        lines = text.split("\n")

        for line in lines:
            clean = line.strip()

            #  Skip very short junk
            if len(clean) < 8:
                continue

            #  Skip noisy patterns
            if re.search(r"\d", clean):   # numbers → skip
                continue

            if "/" in clean or "," in clean:
                continue

            #  Detect Unit / Chapter
            unit_match = re.search(
                r"(Unit\s*\(?\d+\)?|Chapter\s*\d+)",
                clean,
                re.IGNORECASE
            )

            #  Detect proper headings (ALL CAPS, reasonable length)
            heading_match = (
                clean.isupper()
                and 3 <= len(clean.split()) <= 8
                and not clean.endswith("OF")   # avoid broken lines
                and not clean.startswith("INTO")  # OCR junk
            )

            if unit_match:
                chapters[page_num] = clean

            elif heading_match:
                chapters[page_num] = clean

    return chapters

# 6. Embedding + FAISS Index
# ------------------------------------------------------------
def build_faiss_index(chunks):
    texts = [c["text"] for c in chunks]
    embeddings = EMBED_MODEL.encode(texts, convert_to_tensor=False)

    dim = len(embeddings[0])
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    return index, embeddings

# 7. Semantic Search
# ------------------------------------------------------------
#def search(query, chunks, index, k=3):
   # q_emb = EMBED_MODEL.encode([query])[0]
   # D, I = index.search(q_emb.reshape(1, -1), k)
    #return [(chunks[i]["page"], chunks[i]["text"]) for i in I[0]])

def search_with_excerpts(query, chunks, index, k=5):
    q_emb = EMBED_MODEL.encode([query])[0]
    D, I = index.search(q_emb.reshape(1, -1), k)

    results = []
    for i, score in zip(I[0],D[0]):
      if i==-1:
        continue
      results.append({
          "page": chunks[i]["page"],
          "text": chunks[i]["text"],
          "excerpt": " ".join(chunks[i]["text"].split()[:60]) + "...",
          "score" : float(score)
        })
    return results

# 8. Question Answering
# ------------------------------------------------------------
def answer_question(question, context):

    prompt = f"""
You are an academic study assistant.

Using ONLY the provided context, give a detailed explanation
suitable for a university student.
Write a clear explanation suitable for a university student.
Include the following if possible:
• Overview of the topic
• Important subtopics
• Key concepts explained briefly

Structure your answer in the following format:

Definition:
Provide a clear definition of the concept.

Explanation:
Explain the concept in detail using the information from the context.

Example (if applicable):
Give a simple example to help understanding.

Rules:
- Use only the information in the context
- Write clearly and academically
- Do not invent information outside the context

Context:
{context}

Question:
{question}

Detailed Answer:
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return res.choices[0].message.content

# 9. Summarization
# ------------------------------------------------------------
def summarize_text(text, chunk_size=800):

    words = text.split()
    summaries = []

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])

        summary = summarizer(
            chunk,
            max_length=120,
            min_length=40,
            do_sample=False
        )[0]["summary_text"]

        summaries.append(summary)

    final_summary = " ".join(summaries)

        # split into sentences
    sentences = final_summary.split(". ")

    # format nicely
    formatted = "\n\n".join([s.strip() + "." for s in sentences if len(s) > 5])

    return formatted

def summarize_full_pdf(chunks):

    print("Generating full PDF summary...")

    # Take representative chunks (every 20th chunk)
    sampled_chunks = chunks[::20]

    # Combine them
    combined_text = " ".join([c["text"] for c in sampled_chunks])

    # Run summarizer
    result = summarizer(
        combined_text,
        max_length=300,
        min_length=120,
        do_sample=False
    )[0]["summary_text"]

    # break into sentences
    sentences = result.split(". ")

    # format nicely
    formatted = "\n\n".join([s.strip() + "." for s in sentences if len(s) > 5])

    return formatted

def generate_exam(self, chapters=None, num_mcq=5, num_subjective=2, difficulty='medium'):

    if chapters:
        #  try exact match
        chunks = self.get_chunks_by_chapters(chapters)

        # fallback to semantic search
        if not chunks:
            print("Fallback to semantic search")
            query = f"Explain in detail about {chapters[0]}"
            chunks = self.get_chunks_by_topic(query)

    else:
        chunks = self.chunks

    # build context
    context = build_context(chunks, k=5)

    # generate quiz
    quiz = generate_exam_quiz(
        context,
        num_mcq=num_mcq,
        num_subjective=num_subjective
    )

    return quiz

import random

def build_context(chunks, k=5):
    selected = random.sample(chunks, min(k, len(chunks)))
    return " ".join([c["text"] for c in selected])

def generate_exam_quiz(context, num_mcq, num_subjective, difficulty="medium"):
    short_context = context[:1000]
    prompt = f"""
Generate:
- {num_mcq} MCQs (with 4 options and answers)
- {num_subjective} subjective questions with answers

Difficulty level: {difficulty}

Guidelines:
- Easy → basic definitions, direct questions
- Medium → conceptual understanding
- Hard → tricky, application-based questions

Format EXACTLY like this:

Q1. Question
A. option
B. option
C. option
D. option
Answer: A
Explanation: ...

--- SUBJECTIVE ---

Q1. Question
Answer: ...

TEXT:
{short_context}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=900,
        temperature=0.4
    )

    output = response.choices[0].message.content

    return {
        "response": output
    }



'''def render_mermaid(code):
    html = f"""
    <div class="mermaid">
    {code}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
    mermaid.initialize({{ startOnLoad: true }});
    </script>
    """
    display(HTML(html))
'''
# ============================================================

def format_response(question, answer, pages, excerpts, chapter=None):
    formatted = " **QUESTION**\n"
    formatted += f"{question}\n\n"

    formatted += " **ANSWER**\n"
    formatted += f"{answer}\n\n"

    formatted += " **SOURCE PAGES**\n"
    formatted += ", ".join(str(p) for p in pages) + "\n\n"

    if chapter:
        formatted += " **CHAPTER**\n"
        formatted += f"{chapter}\n\n"

    formatted += " **EXCERPTS**\n"
    for pg, text in excerpts:
        short = text[:200].replace("\n", " ") + "..."
        formatted += f"- **Pg {pg}:** {short}\n"

    return formatted

def format_quiz(quiz):
    if not quiz:
        print("❌ Quiz generation failed")
        return

    lines = quiz.split("\n")

    for line in lines:
        line = line.strip()

        if line.startswith("Q"):
            print(f"\n {line}")

        elif line.startswith(("A.", "B.", "C.", "D.")):
            print(f"   {line}")

        elif "Answer:" in line:
            print(f"    {line}")

        elif "Explanation:" in line:
            print(f"    {line}")

        elif "--- SUBJECTIVE ---" in line:
            print("\n SUBJECTIVE QUESTIONS\n")

        elif line.startswith("Answer"):
            print(f"    {line}")

        else:
            print(line)

# ------------------------------------------------------------
# Intent Detection (ADD HERE)
# ------------------------------------------------------------
def is_diagram_request(question):
    keywords = ["diagram", "flowchart", "flow chart", "visualize", "draw"]
    return any(k in question.lower() for k in keywords)

def find_index_pages(pages):
    index_pages = []
    found = False

    for page_num, text in pages[:15]:
        clean = text.lower()

        # detect start
        if "table of contents" in clean:
            found = True

        # collect pages after start
        if found:
            index_pages.append(text)

            # stop if no numbered lines anymore
            if not any(line.strip().startswith(tuple(str(i) for i in range(1, 10)))
                       for line in text.split("\n")):
                break

    return index_pages

import re

def extract_from_index(text):
    chapters = []

    lines = text.split("\n")

    for line in lines:
        clean = line.strip()

        # match numbered lines
        if re.match(r"^\d+", clean):

            # remove leading number
            title = re.sub(r"^\d+\s*[\.\)]?\s*", "", clean)

            # remove dots
            title = re.sub(r"\s*\.+\s*", " ", title)

            #  remove trailing page numbers (FIX)
            title = re.sub(r"\s+\d+$", "", title)

            # clean spacing
            title = " ".join(title.split())

            #  relaxed filter (IMPORTANT)
            if 2 <= len(title.split()) <= 15:
                chapters.append(title)

    return chapters

# 12.Full Pipeline Function
# ------------------------------------------------------------
class SmartStudyAgent:
    def __init__(self):
        self.chunks = None
        self.index = None
        self.chapters = None

    def load_pdf(self, path):
        pages, error = read_pdf(path)

        if error == "EMPTY_OR_IMAGE_PDF":
            print(" This PDF has no readable text.")
            print(" It may be empty or contain only images.")
            print(" Please upload a text-based PDF.")
            self.chunks = None
            self.index = None
            self.chapters = None
            return
        if not pages:
            self.chunks = None
            self.index = None
            self.chapters = None
            return

        #  NEW MULTI-PAGE INDEX LOGIC
        index_pages = find_index_pages(pages)

        if index_pages:
            print("Index detected!")

            full_index_text = "\n".join(index_pages)

            extracted = extract_from_index(full_index_text)

            if len(extracted) > 0:
                self.chapters = {i: ch for i, ch in enumerate(extracted)}
            else:
                print("Index parsing failed → fallback to detection")
                self.chapters = detect_chapters(pages)

        else:
            print("No index found → using detection")
            self.chapters = detect_chapters(pages)

        self.chunks = chunk_text(pages, self.chapters)
        self.index, _ = build_faiss_index(self.chunks)

        print("PDF Loaded + Indexed Successfully!")


    def ask(self, question):
        if is_diagram_request(question):
            results = search_with_excerpts(question, self.chunks, self.index)
            top_chunks = sorted(results, key=lambda x: x["score"])[:3]
            context = " ".join([r["text"] for r in top_chunks])

            answer = answer_question(question, context)
            diagram = self.diagram(answer)
            return {
                "type": "diagram",
                "diagram": diagram
            }

        results = search_with_excerpts(question, self.chunks, self.index)
          # ---------------- CONFIDENCE SCORE ----------------
        scores = [r["score"] for r in results if "score" in r]

        if scores:
            best_distance = min(scores)    # average similarity (0–1)
            confidence = 1 / (1 + best_distance)
        else:
            confidence = 0.0

        confidence_pct = round(confidence * 100, 1)  # convert to %
        # -------------------------------------------------
        # Context for QA
        context = " ".join([r["text"] for r in results[:5]])

        # Pages
        pages = [r["page"] for r in results]

        # Run QA model
        answer = answer_question(question, context)

        # Excerpts
        excerpts = [
            {
                "page": r["page"],
                "excerpt": r["excerpt"]
            }
            for r in results
        ]

        # Chapter
        chapter = None
        for p in pages:
            if p in self.chapters:
                chapter = self.chapters[p]
                break

        # Markdown formatting (presentation layer)
        formatted = (
f"##  Answer\n\n"
f"{answer}\n\n"
f"---\n"
f"###  Confidence\n"
f"{confidence_pct}%\n\n"
f"###  Source Pages\n"
f"{', '.join(str(p) for p in pages)}\n\n"
f"###  Supporting Excerpts\n"
+ "\n".join([f"- **Pg {e['page']}**: {e['excerpt']}" for e in excerpts])
)
        if chapter:
            formatted += f"\n\n **Chapter:** {chapter}"

      # STRUCTURED RETURN
        return {
            "type": "answer",
            "answer": answer,
            "pages": pages,
            "context": context,
            "excerpts": excerpts,
            "chapter": chapter,
            "confidence": confidence_pct,
            "formatted": formatted
        }

    def visualize(self, query):
        if self.index is None or self.chunks is None:
            text = query   # fallback (no PDF loaded)

        else:
            results = search_with_excerpts(query, self.chunks, self.index)

            if results:
                text = " ".join([r["text"] for r in results[:3]])
            else:
                text = query

        diagram = self.diagram(text)

        return {
            "diagram": diagram,
            "text": text
        }
    def get_chunks_by_chapters(self, selected_chapters):
        filtered = []

        for chunk in self.chunks:
            for ch in selected_chapters:
                if ch.lower() in chunk["chapter"].lower():
                    filtered.append(chunk)

        return filtered
    def get_chunks_by_topic(self, topic, k=8):
        results = search_with_excerpts(topic, self.chunks, self.index, k=k)
        return [r for r in results]
    def generate_exam(self, chapters=None, num_mcq=5, num_subjective=2,difficulty='medium'):
        if not self.chunks:
            return {"response": "Please upload or select a valid PDF first"}
        if chapters:
            #  try exact match
            chunks = self.get_chunks_by_chapters(chapters)

            # fallback to semantic search
            if not chunks:
                print("Fallback to semantic search")
                query = f"Explain in detail about {chapters[0]}"
                chunks = self.get_chunks_by_topic(query)

        else:
            chunks = self.chunks

        # build context
        context = build_context(chunks, k=5)

        # generate quiz
        quiz = generate_exam_quiz(
            context,
            num_mcq=num_mcq,
            num_subjective=num_subjective
        )

        return quiz
    def summarize(self):
        if not self.chunks:
            return "Please upload a PDF first"

        #  take top chunks (important content)
        combined_text = " ".join([c["text"] for c in self.chunks[:10]])

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"""
    Summarize the following content into clean bullet points.

    STRICT FORMAT:
    • Point 1  
    • Point 2  
    • Point 3  

    Rules:
    - No headings
    - No paragraphs
    - Only bullet points
    - Keep it concise and clear

    Text:
    {combined_text}
    """
            }]
        )

        return response.choices[0].message.content

    def summarize_pdf(self):
        return summarize_full_pdf(self.chunks)

    def diagram(self, text):
        return generate_diagram(text)
    def list_chapters(self):
        seen = set()
        ordered = []

        for page in sorted(self.chapters.keys()):
            ch = self.chapters[page]

            if ch not in seen:
                ordered.append(ch)
                seen.add(ch)

        return ordered

print("\nSMART STUDY AGENT READY!")
from PyPDF2 import PdfReader
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO


def extract_text_from_pdf(file):

    reader = PdfReader(file.file)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def chunk_text(text, chunk_size=500, overlap=50):

    words = text.split()

    chunks = []

    start = 0

    page = 1

    while start < len(words):

        end = start + chunk_size

        chunk_words = words[start:end]

        chunk = " ".join(chunk_words)

        chunks.append({
            "page": page,
            "text": chunk
        })

        start = end - overlap

        page += 1

    return chunks

def generate_assignment_pdf(assignment):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    doc.title = assignment["title"]

    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph(f"Title: {assignment['title']}", styles['Title']))
    content.append(Paragraph(f"Course: {assignment['course_name']}", styles['Normal']))
    content.append(Paragraph(f"Teacher: {assignment['teacher_name']}", styles['Normal']))
    content.append(Paragraph(f"Due Date: {assignment['due_date']}", styles['Normal']))

    content.append(Paragraph("Instructions:", styles['Heading2']))
    content.append(Paragraph(assignment['instructions'], styles['Normal']))

    content.append(Paragraph("Questions:", styles['Heading2']))

    for i, q in enumerate(assignment['questions']):
        content.append(
            Paragraph(f"{i+1}. {q['question']} ({q['marks']} marks)", styles['Normal'])
        )

    doc.build(content)
    buffer.seek(0)

    return buffer.read()
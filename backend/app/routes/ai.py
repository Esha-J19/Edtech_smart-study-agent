from fastapi import APIRouter
from app.utils.ai_utils import summarize_text, answer_question, generate_quiz, generate_diagram

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/summarize")
def summarize_api(data: dict):
    return {"result": summarize_text(data["text"])}


@router.post("/qa")
def qa_api(data: dict):
    return {
        "result": answer_question(
            data["question"],
            data["context"]
        )
    }


@router.post("/quiz")
def quiz_api(data: dict):
    return {"result": generate_quiz(data["text"])}


@router.post("/diagram")
def diagram_api(data: dict):
    return {"result": generate_diagram(data["text"])}
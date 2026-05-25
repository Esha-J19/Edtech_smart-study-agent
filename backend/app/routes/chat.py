from backend.app.utils.ai_engine.ai_engine import agent
from fastapi import APIRouter, Request
from backend.app.store import SESSION_STORE

router = APIRouter(prefix="/chat", tags=["Chat"])


# ---------------- ASK QUESTION ----------------

from pydantic import BaseModel

class AskRequest(BaseModel):
    prompt: str


@router.post("/ask")
async def ask(request: Request):

    try:
        data = await request.json()
    except:
        form = await request.form()
        data = dict(form)

    prompt = data.get("prompt") or data.get("message")

    if not prompt:
        return {"response": "No question provided"}

    
    if not SESSION_STORE.get("pdf_uploaded"):
        return {"response": "Please upload a PDF first"}

    if "summarize" in prompt.lower():
        response = agent.summarize()
        return {"response": response}

    else:
        result = agent.ask(prompt)
        return {"response": result["formatted"]}


@router.post("/quiz")
async def quiz(data: dict):
    try:
        topic = data.get("topic")
        num_mcq = data.get("num_mcq", 3)
        num_subjective = data.get("num_subjective", 1)
        difficulty = data.get("difficulty", "medium")

        if not topic:
            return {"response": "Please provide a topic"}

        quiz = agent.generate_exam(
            chapters=[topic],
            num_mcq=num_mcq,
            num_subjective=num_subjective,
            difficulty=difficulty
        )

        return {"response": quiz["response"]}

    except Exception as e:
        return {"response": str(e)}
    

# ---------------- DIAGRAM ----------------

@router.post("/diagram")
async def diagram(data: dict):

    text = data.get("text")

    if not text:
        return {"response": "No text provided"}

    diagram = agent.diagram(text)

    return {"response": diagram}

@router.post("/visualize")
async def visualize(data: dict):
    query = data.get("text")

    if not query:
        return {"response": "No text provided"}

    result = agent.visualize(query)

    return result
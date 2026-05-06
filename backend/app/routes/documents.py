print(" DOCUMENTS FILE RUNNING ")
from app.utils.ai_engine.ai_engine import agent
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime
import os

from bson import ObjectId
from fastapi.responses import Response

from app.database import documents_collection, classrooms_collection
from app.auth_utils import get_current_user

router = APIRouter(prefix="/documents", tags=["Documents"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


# ---------------- UPLOAD DOCUMENT ----------------
from app.store import SESSION_STORE
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    class_code: str = Form(...),
    title: str = Form(...),
    material_type: str = Form(...),
    class_name: str = Form(...),
    token: str = Depends(oauth2_scheme)   
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        print("PAYLOAD:", payload)   

        email = payload.get("sub")
        role = payload.get("role")

        print("EMAIL:", email)

        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        # ---------- READ FILE ----------
        file_bytes = await file.read()
        SESSION_STORE.clear()
        SESSION_STORE["pdf_uploaded"] = True 
        try:
            agent.reset()
        except:
            pass   
        file_path = f"temp_{file.filename}"

        with open(file_path, "wb") as f:
            f.write(file_bytes)
        # load into AI system
        agent.load_pdf(file_path)
        # ---------- SAVE TO DATABASE ----------
        doc = {
            "filename": file.filename,
            "content_type": file.content_type,
            "data": file_bytes,
            "uploaded_by": email,
            "role": role,
            "class_code": class_code,
            "class_name": class_name,
            "title": title,
            "type": material_type,
            "uploaded_at": datetime.utcnow()
        }

        documents_collection.insert_one(doc)

        return {
            "message": "Document uploaded successfully"
        }

    except Exception as e:
        print("UPLOAD ERROR:", str(e))  
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- GET DOCUMENTS (TEACHER) ----------------

@router.get("/")
async def get_documents(token: str = Depends(oauth2_scheme)):

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email = payload.get("sub")

    docs = documents_collection.find({"uploaded_by": email})

    result = []

    for d in docs:
        result.append({
            "id": str(d["_id"]),
            "filename": d["filename"],
            "content_type": d["content_type"],
            "uploaded_at": d["uploaded_at"]
        })

    return {"documents": result}


# ---------------- STUDENT MATERIAL ----------------

@router.get("/student-material")
def get_material(user=Depends(get_current_user)):

    classes = classrooms_collection.find({
        "students": user["email"]
    })

    class_codes = [c["code"] for c in classes]

    docs = documents_collection.find({
        "class_code": {"$in": class_codes}
    })

    result = []
    for d in docs:
        d["_id"] = str(d["_id"])
        d.pop("data", None)   # remove heavy file data
        result.append(d)

    return result


# ---------------- VIEW FILE ----------------

@router.get("/file/{id}")
def get_file(id: str):

    doc = documents_collection.find_one({"_id": ObjectId(id)})

    if not doc:
        raise HTTPException(status_code=404, detail="File not found")

    return Response(
        content=doc["data"],
        media_type=doc["content_type"],
        headers={
            "Content-Disposition": "inline"
        }
    )
@router.post("/ask-from-docs")
def ask_from_docs(data: dict):

    print("DOC_IDS RECEIVED:", data.get("doc_ids"))
    print("FULL DATA:", data)
    doc_ids = data.get("doc_ids", [])

    if not doc_ids:
        return {"response": "Please select at least one PDF"}

    question = data.get("question")

    contexts = []

    for doc_id in doc_ids:
        try:
            doc = documents_collection.find_one({"_id": ObjectId(doc_id)})
            if not doc:
                continue

            file_path = "temp.pdf"

            with open(file_path, "wb") as f:
                f.write(doc["data"])

            agent.load_pdf(file_path)

            
            summary = agent.ask("Summarize this document in 5 lines")
            contexts.append(str(summary))

        except Exception as e:
            print("ERROR:", e)

    #  combine all PDFs
    combined_context = "\n\n".join(contexts)

    #  final smart answer
    final_prompt = f"""
    Answer in 4-5 bullet points using the following documents:

    {combined_context}

    Question: {question}
    """

    result = agent.ask(final_prompt)

    #  safe handling
    if isinstance(result, dict):
        response = result.get("formatted") or result.get("response") or str(result)
    else:
        response = str(result)

    return {"response": response}
'''@router.post("/ask-from-docs")
def ask_from_docs(data: dict):
    print("DOC_ID RECEIVED:", data.get("doc_id"))
    doc_id = data.get("doc_id")

    if not doc_id:
        return {"response": "Please select a PDF first"}

    try:
        doc = documents_collection.find_one({"_id": ObjectId(doc_id)})
    except Exception as e:
        return {"response": "Invalid document ID"}

    if not doc:
        return {"response": "Document not found"}

    #  load correct PDF into agent
    file_path = f"temp_{doc['filename']}"

    with open(file_path, "wb") as f:
        f.write(doc["data"])

    agent.reset()
    agent.load_pdf(file_path)

    result = agent.ask(data["question"])

    #  safe handling
    if isinstance(result, dict):
        response = result.get("formatted") or result.get("response") or str(result)
    else:
        response = str(result)

    return {"response": response}'''
#-----------------Doc-->QuizGenerator-------
from bson import ObjectId

@router.post("/generate-quiz")
async def generate_quiz_from_doc(data: dict):

    document_ids = data.get("document_ids", [])
    num_mcq = data.get("num_mcq", 10)
    difficulty = data.get("difficulty", "medium")

    try:
        try:
            agent.reset()
        except:
            pass

        contexts = []
        seen = set()   # duplicate remove

        for doc_id in document_ids:

            doc = documents_collection.find_one({"_id": ObjectId(doc_id)})
            if not doc:
                continue

            file_path = f"temp_{doc['filename']}"

            with open(file_path, "wb") as f:
                f.write(doc["data"])

            agent.load_pdf(file_path)

            #  BETTER: extract DIFFERENT info
            raw = agent.ask(
                "Give unique key topics, concepts, and definitions from this document (no repetition)"
            )

            if isinstance(raw, dict):
                content = raw.get("formatted") or raw.get("response")
            elif isinstance(raw, str):
                content = raw
            else:
                content = ""

            if not isinstance(content, str):
                content = str(content)

            if content.strip() == "..." or content.strip() == "":
                continue
    

                contexts.append(content)

        combined_context = "\n\n".join(contexts)

        #  SUPER STRICT PROMPT
        prompt = f"""
You are a STRICT quiz generator.

RULES:
- NO duplicate questions
- Each question must test a DIFFERENT concept
- NO repeated options
- Clean formatting ONLY

FORMAT EXACTLY LIKE THIS:

Q1. Question
A) Option
B) Option
C) Option
D) Option
Answer: Correct Option
Explanation: Short explanation

Generate {num_mcq} MCQs from:

{combined_context}
"""

        result = agent.ask(prompt)

        #  CLEAN BACKEND OUTPUT
        if isinstance(result, dict):
            response = result.get("formatted") or result.get("response") or str(result)
        else:
            response = str(result)

        return {"response": response}

    except Exception as e:
        return {"response": str(e)}
#------------DELETEE--IN---STUDENT Q/A--------------------
@router.delete("/delete/{id}")
def delete_document(id: str, user=Depends(get_current_user)):

    doc = documents_collection.find_one({"_id": ObjectId(id)})

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    #  security (optional but good)
    if doc["uploaded_by"] != user["email"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    documents_collection.delete_one({"_id": ObjectId(id)})

    return {"message": "Deleted successfully"}
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# load .env variables
load_dotenv()

# ---------- ROUTES IMPORT ----------
from backend.app.routes import auth
from backend.app.routes import documents
from backend.app.routes.chat import router as chat_router
from backend.app.routes import teacher
from backend.app.routes import student
from backend.app.routes import classroom
from backend.app.routes import announcements
from backend.app.routes import ai  
from backend.app.routes import quiz 

# ---------- APP ----------
app = FastAPI()

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- ROUTES ----------
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat_router)
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(classroom.router)
app.include_router(announcements.router)
#app.include_router(ai.router)  
app.include_router(quiz.router)

# ---------- ROOT ----------
@app.get("/")
def root():
    return {"status": "Backend running "}
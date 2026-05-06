from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# load .env variables
load_dotenv()

# ---------- ROUTES IMPORT ----------
from app.routes import auth
from app.routes import documents
from app.routes.chat import router as chat_router
from app.routes import teacher
from app.routes import student
from app.routes import classroom
from app.routes import announcements
from app.routes import ai  
from app.routes import quiz 

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
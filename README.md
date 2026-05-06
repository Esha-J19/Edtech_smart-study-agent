# Edtech_smart-study-agent
AI-based EdTech platform for smart learning, quizzes, and classroom management

##  Project Overview
Smart Study Agent is an AI-powered educational platform that combines intelligent learning features with classroom management. It allows students and teachers to interact with study materials in a structured, efficient, and interactive way.

The system transforms static content such as PDFs, notes, and documents into dynamic learning resources using AI. It provides features like summarization, question answering, quiz generation, and visualization. Along with this, it supports classroom management including assignments, quizzes, and announcements.

Overall, the platform improves learning efficiency and provides a smart, organized, and user-friendly academic environment.

---

##  Key Features

###  Student
- Register and login securely  
- Join classroom using class code  
- Upload documents and use AI features  
- View study materials  
- Attempt quizzes and view results  
- Submit assignments  
- View announcements  

###  Teacher
- Create classroom and generate class code  
- Upload study materials  
- Create quizzes and assignments  
- Post announcements  
- View student submissions  
- Monitor quiz scores and performance  

### AI Features
- Document summarization  
- Question answering  
- Automatic quiz generation  
- Concept visualization (flowcharts/diagrams)  

###  Common Features
- Role-based access control  
- Error handling and validation  
- User-friendly dashboard  

---

##  Technologies Used

### Frontend
- HTML, CSS, JavaScript  

### Backend
- FastAPI  
- Uvicorn  

### Database
- MongoDB Atlas  

### AI/ML Tools
- Sentence Transformers  
- FAISS  
- OpenAI API  
- LangChain  

### Development Tools
- VS Code  
- Git & GitHub  
- Postman  

---

##  Project Structure

smart-study-agent/
│
├── smart-study-agent-backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── ai.py
│   │   │   ├── announcements.py
│   │   │   ├── auth.py
│   │   │   ├── chat.py
│   │   │   ├── classroom.py
│   │   │   ├── documents.py
│   │   │   ├── quiz.py
│   │   │   ├── student.py
│   │   │   ├── teacher.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── utils/
│   │   │   ├── ai_engine/
│   │   │   │   ├── ai_engine.py
│   │   │   │   └── smart_study_agent.py
│   │   │   │
│   │   │   ├── ai_utils.py
│   │   │   ├── email_service.py
│   │   │   ├── jwt.py
│   │   │   ├── pdf_utils.py
│   │   │   ├── security.py
│   │   │   ├── utils.py
│   │   │   └── __init__.py
│   │   │
│   │   ├── auth_utils.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── otp_store.py
│   │   ├── store.py
│   │   ├── main.py
│   │   └── __init__.py
│   │
│   ├── requirements.txt
│   ├── .env
│   └── venv/
│
├── smart-study-agent-frontend/
│   ├── (HTML Pages)
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── join-class.html
│   │   ├── my-assignments.html
│   │   ├── quiz-results.html
│   │   ├── class.html
│   │   ├── class-details.html
│   │   └── announcement.html
│   │
│   ├── assets/
│   ├── videos/
│   ├── images/
│   └── other UI files
│
└── README.md


## Setup Instructions

## Frontend
```bash
cd frontend
npm install
npm start

## Backend (FastAPI)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

System Workflow
Teacher creates classroom
Student joins using class code
Teacher uploads materials, assignments, quizzes
AI processes documents (summarization, QA, quiz generation)
Student interacts with content
System generates results and reports

Testing
Unit Testing (modules testing)
Integration Testing (frontend + backend)
System Testing (end-to-end workflow)
API Testing using Postman


Future Enhancements
Mobile application
AI-based personalized learning
Advanced analytics dashboard
Voice-based interaction
Multi-language support


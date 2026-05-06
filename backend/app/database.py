from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("MONGO_URI not found in environment variables")

client = MongoClient(MONGO_URI)
db = client["smart_study_agent"]

# ---- Collections only ----
users_collection = db["users"]
documents_collection = db["documents"]
quizzes_collection = db["quizzes"]
leaderboard_collection = db["leaderboards"]
chats_collection = db["chats"]
messages_collection = db["messages"]
assignments_collection = db["assignments"]
classrooms_collection = db["classrooms"]
submissions_collection = db["submissions"]
announcements_collection = db["announcements"]
quizzes_collection = db["quizzes"]
submissions_collection = db["quiz_submissions"]


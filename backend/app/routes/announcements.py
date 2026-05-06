from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os

from app.database import announcements_collection
from app.auth_utils import get_current_user
from app.database import classrooms_collection

router = APIRouter(prefix="/announcements", tags=["Announcements"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


#  CREATE ANNOUNCEMENT (Teacher only)
@router.post("/create")
def create_announcement(data: dict, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")

        if role != "teacher":
            raise HTTPException(status_code=403, detail="Only teachers allowed")

        announcement = {
            "title": data.get("title"),
            "message": data.get("message"),
            "course": data.get("course"),  
            "type": data.get("type"),
            "class_code": data.get("class_code"), 
            "created_by": email,
            "created_at": datetime.utcnow()
        }

        announcements_collection.insert_one(announcement)

        return {"message": "Announcement created"}

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# 🔹 GET ALL ANNOUNCEMENTS (Students)
@router.get("/all")
def get_announcements(course: str = None):
    query = {}

    if course:
        query["course"] = course   

    announcements = list(
        announcements_collection.find(query).sort("created_at", -1)
    )

    for a in announcements:
        a["_id"] = str(a["_id"])

    return {"announcements": announcements}

@router.get("/student")
def get_student_announcements(user=Depends(get_current_user)):

    classes = classrooms_collection.find({
        "students": user["email"]
    })

    class_codes = [c["code"] for c in classes]

    announcements = announcements_collection.find({
        "class_code": {"$in": class_codes}
    }).sort("created_at", -1)

    result = []
    for a in announcements:
        a["_id"] = str(a["_id"])
        result.append(a)

    return result
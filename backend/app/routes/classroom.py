from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
import random
import string

from backend.app.database import db
from backend.app.auth_utils import get_current_user

router = APIRouter(prefix="/classroom", tags=["Classroom"])

classrooms_collection = db["classrooms"]


#  Generate class code
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


# ---------------- CREATE CLASS ----------------
@router.post("/create")
def create_classroom(data: dict, user=Depends(get_current_user)):

    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teacher can create classroom")

    code = generate_code()

    classroom = {
        "name": data.get("name"),
        "teacher": user["email"],
        "code": code,
        "students": [],
        "created_at": datetime.utcnow()
    }

    classrooms_collection.insert_one(classroom)

    return {
        "message": "Classroom created",
        "code": code
    }


# ---------------- JOIN CLASS ----------------
@router.post("/join")
def join_classroom(data: dict, user=Depends(get_current_user)):

    code = data.get("code")

    classroom = classrooms_collection.find_one({"code": code})

    if not classroom:
        raise HTTPException(status_code=404, detail="Invalid class code")

    classrooms_collection.update_one(
        {"code": code},
        {"$addToSet": {"students": user["email"]}}
    )

    return {"message": "Joined classroom successfully"}


# ---------------- GET MY CLASSES ----------------
@router.get("/my")
def get_my_classes(user=Depends(get_current_user)):

    if user["role"] == "teacher":
        classes = classrooms_collection.find({"teacher": user["email"]})
    else:
        classes = classrooms_collection.find({"students": user["email"]})

    result = []
    for c in classes:
        c["_id"] = str(c["_id"])
        result.append(c)

    return result
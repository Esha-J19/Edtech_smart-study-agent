from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from app.database import assignments_collection
from app.auth_utils import get_current_user
from app.utils.pdf_utils import generate_assignment_pdf
from fastapi.responses import Response
from bson import ObjectId
from app.database import submissions_collection
from app.database import classrooms_collection

router = APIRouter(prefix="/teacher", tags=["Teacher"])

# ---------------- CREATE ASSIGNMENT ----------------
@router.post("/assignment")
def create_assignment(data: dict, user=Depends(get_current_user)):

    #  Only teacher allowed
    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teacher can create assignment")

    #  Basic validation
    if not data.get("title") or not data.get("course_name"):
        raise HTTPException(status_code=400, detail="Missing required fields")

    assignment = {
        "course_name": data.get("course_name"),
        "teacher_name": data.get("teacher_name"),
        "assignment_number": data.get("assignment_number"),
        "date": data.get("date"),
        "due_date": data.get("due_date"),
        "title": data.get("title"),
        "instructions": data.get("instructions"),
        "questions": data.get("questions", []),

        "created_by": user["email"],
        "created_at": datetime.utcnow(),

        # future use (student targeting)
        "class_name": data.get("class_name"),
        "class_code": data.get("class_code")
    }
    assignment["_id"] = ObjectId() 
    assignment.pop("_id", None)
    pdf_bytes = generate_assignment_pdf(assignment)
    assignment["pdf"] = pdf_bytes

    try:
        result = assignments_collection.insert_one(assignment)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Assignment saved successfully",
        "assignment_id": str(result.inserted_id)
    }


@router.get("/submissions/{assignment_id}")
def get_submissions(assignment_id: str):

    submissions = submissions_collection.find({
        "assignment_id": assignment_id
    })

    result = []

    for s in submissions:
        s["_id"] = str(s["_id"])
        s.pop("file", None)  # heavy data remove
        result.append(s)

    return result


@router.get("/class-assignments/{class_code}")
def get_class_assignments(class_code: str):

    assignments = assignments_collection.find({
        "class_code": class_code
    })

    result = []

    for a in assignments:
        a["_id"] = str(a["_id"])
        a.pop("pdf", None)   
        result.append(a)

    return result

@router.delete("/assignment/{id}")
def delete_assignment(id: str, user=Depends(get_current_user)):

    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Not allowed")

    #  delete assignment
    assignments_collection.delete_one({
        "_id": ObjectId(id),
        "created_by": user["email"]
    })

    #  delete all submissions of that assignment 
    submissions_collection.delete_many({
        "assignment_id": id
    })

    return {"message": "Assignment + submissions deleted "}

@router.get("/submission-file/{id}")
def get_submission_file(id: str):

    try:
        # validate ObjectId
        if not ObjectId.is_valid(id):
            raise HTTPException(status_code=400, detail="Invalid ID")

        sub = submissions_collection.find_one({"_id": ObjectId(id)})

        if not sub:
            raise HTTPException(status_code=404, detail="Submission not found")

        if "file" not in sub:
            raise HTTPException(status_code=404, detail="File not found")

        return Response(
            content=sub["file"],
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline"
            }
        )

    except Exception as e:
        print(" DOWNLOAD ERROR:", e)
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/classroom/{code}")
def delete_classroom(code: str, user=Depends(get_current_user)):

    classroom = classrooms_collection.find_one({"code": code})

    if not classroom:
        raise HTTPException(status_code=404, detail="Class not found")

    classrooms_collection.delete_one({"code": code})

    assignments_collection.delete_many({"class_code": code})
    submissions_collection.delete_many({"class_code": code})

    return {"message": "Class deleted"}
from fastapi import APIRouter, Depends
from backend.app.database import assignments_collection
from backend.app.auth_utils import get_current_user
from fastapi.responses import Response
from bson import ObjectId
from backend.app.database import classrooms_collection

from fastapi import UploadFile, File
from datetime import datetime
from backend.app.database import submissions_collection


router = APIRouter(prefix="/student", tags=["Student"])


@router.get("/assignments")
def get_assignments(user=Depends(get_current_user)):

    #  step 1: find student classes
    classes = classrooms_collection.find({
        "students": user["email"]
    })

    class_codes = [c["code"] for c in classes]

    #  step 2: find assignments
    assignments = assignments_collection.find({
        "class_code": {"$in": class_codes}
    })

    result = []

    for a in assignments:
        a["_id"] = str(a["_id"])
        a.pop("pdf", None)
        result.append(a)

    return result

@router.get("/assignment-pdf/{id}")
def get_pdf(id: str):

    assignment = assignments_collection.find_one({"_id": ObjectId(id)})

    if not assignment or "pdf" not in assignment:
        raise HTTPException(status_code=404, detail="PDF not found")

    return Response(
        content=assignment["pdf"],
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline"  
        }
    )

@router.post("/submit-assignment/{assignment_id}")
async def submit_assignment(
    assignment_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):

    content = await file.read()

    submission = {
        "assignment_id": assignment_id,
        "student_email": user["email"],
        "file_name": file.filename,
        "file": content,
        "submitted_at": datetime.utcnow()
    }

    submissions_collection.insert_one(submission)

    return {"message": "Submitted successfully "}

@router.get("/submission-file/{id}")
def get_submission_file(id: str):

    sub = submissions_collection.find_one({"_id": ObjectId(id)})

    return Response(
        content=sub["file"],
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": "inline"   
        }
    )

@router.post("/classroom/leave/{code}")
def leave_class(code: str, user=Depends(get_current_user)):

    classrooms_collection.update_one(
        {"code": code},
        {"$pull": {"students": user["email"]}}
    )

    return {"message": "Left classroom"}
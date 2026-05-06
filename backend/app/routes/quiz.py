from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.database import quizzes_collection, classrooms_collection
from app.auth_utils import get_current_user
from bson import ObjectId
from datetime import datetime, timedelta
from app.database import submissions_collection  
from fastapi.encoders import jsonable_encoder 

router = APIRouter(prefix="/quiz", tags=["Quiz"])

# CREATE QUIZ
@router.post("/create")
def create_quiz(data: dict, user=Depends(get_current_user)):

    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teacher allowed")

    quiz = {
        "title": data["title"],
        "subject": data["subject"],
        "time_limit": int(data["time_limit"]),
        "questions": data["questions"],
        "class_code": data["class_code"],
        "created_by": user["email"],
        "created_at": datetime.utcnow(),
        "deadline": datetime.utcnow() + timedelta(minutes=int(data["time_limit"]))  
    }

    quizzes_collection.insert_one(quiz)

    return {"message": "Quiz created"}

@router.get("/student")
def get_quiz(user=Depends(get_current_user)):

    classes = classrooms_collection.find({
        "students": user["email"]
    })

    class_codes = [c["code"] for c in classes]

    quizzes = quizzes_collection.find({
        "class_code": {"$in": class_codes}
    })

    result = []

    for q in quizzes:
        q["_id"] = str(q["_id"])

        #  Class name
        class_obj = classrooms_collection.find_one({"code": q["class_code"]})
        q["class_name"] = class_obj["name"] if class_obj else "Class"

        #  Remaining time
        if "deadline" not in q:
            q["remaining_time"] = 0
        else:
            remaining = (q["deadline"] - datetime.utcnow()).total_seconds()
            q["remaining_time"] = max(0, int(remaining))

        #  Attempt check
        existing = submissions_collection.find_one({
            "student": user["email"],
            "quiz_id": str(q["_id"])
        })

        if existing:
            q["attempted"] = True
            q["score"] = existing["score"]
        else:
            q["attempted"] = False

        result.append(q)

    return result   


@router.post("/submit")
def submit_quiz(data: dict, user=Depends(get_current_user)):

    quiz = quizzes_collection.find_one({"_id": ObjectId(data["quiz_id"])})

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    #  Prevent reattempt
    existing = submissions_collection.find_one({
        "student": user["email"],
        "quiz_id": data["quiz_id"]
    })

    if existing:
        raise HTTPException(status_code=400, detail="Already attempted")

    #  Time check
    if datetime.utcnow() > quiz["deadline"]:
        raise HTTPException(status_code=400, detail="Time over")

    score = 0
    result = []

    for i, q in enumerate(quiz["questions"]):

        user_ans = data["answers"][i] if i < len(data["answers"]) else None
        correct_index = ord(q["correct"]) - 65   # A->0, B->1
        correct_ans = q["options"][correct_index]

        user_ans = data["answers"][i] if i < len(data["answers"]) else None

        if user_ans:
            user_index = ord(user_ans) - 65
            user_ans_text = q["options"][user_index]
        else:
            user_ans_text = None

        is_correct = user_ans == correct_ans

        if is_correct:
            score += 1

        result.append({
    "question": q["question"],
    "your_answer": user_ans_text,
    "correct_answer": correct_ans,
    "is_correct": user_ans == q["correct"]
})

    #  Save submission (IMPORTANT)
    submission = {
        "student": user["email"],
        "quiz_id": data["quiz_id"],
        "score": score,
        "answers": data["answers"],
        "submitted_at": datetime.utcnow()
    }

    submissions_collection.insert_one(submission)

    return {
        "score": score,
        "total": len(quiz["questions"]),
        "result": result
    }

@router.get("/quiz-results/{quiz_id}")
def get_quiz_results(quiz_id: str, user=Depends(get_current_user)):

    if user["role"] != "teacher":
        raise HTTPException(status_code=403)

    results = list(submissions_collection.find({
        "quiz_id": quiz_id
    }))

    for r in results:
        r["_id"] = str(r["_id"])

    return results


@router.get("/teacher/results")
def get_all_results(user=Depends(get_current_user)):

    if user["role"] != "teacher":
        raise HTTPException(status_code=403)

    quizzes = list(quizzes_collection.find({
        "created_by": user["email"]
    }))

    final = []

    for q in quizzes:
        quiz_id = str(q["_id"])

        submissions = list(submissions_collection.find({
            "quiz_id": quiz_id
        }))

        #  CLEAN EVERYTHING
        for s in submissions:
            s["_id"] = str(s["_id"])
            if "submitted_at" in s:
                s["submitted_at"] = str(s["submitted_at"])

        final.append({
            "quiz_id": quiz_id,
            "title": q.get("title"),
            "submissions": submissions
        })

    return jsonable_encoder(final)
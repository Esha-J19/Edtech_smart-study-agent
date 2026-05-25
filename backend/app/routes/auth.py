from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timedelta
import random
import os
import re   

from backend.app.database import users_collection
from backend.app.utils.security import verify_password, hash_password
from backend.app.utils.jwt import create_access_token
from abackend.app.utils.email_service import send_otp

STUDENT_REGEX = r"^btbt[a-z0-9_]*@banasthali\.in$"
TEACHER_REGEX = r"^(?!btbt)[a-z0-9._]+@banasthali\.in$"



router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# ---------------- TEMP OTP STORE ----------------
otp_store = {}

# ---------------- SEND OTP ----------------
@router.post("/send-otp")
def send_otp_route(data: dict):
    email = data.get("email")
    role = data.get("role")  

    if not email or not role:
        raise HTTPException(status_code=400, detail="Email and role required")

    email = email.lower()

    # -------- BLOCK RANDOM EMAILS HERE --------
    if role == "student":
        if not re.match(STUDENT_REGEX, email):
            raise HTTPException(
                status_code=400,
                detail="Student email must start with btbt and end with @banasthali.in"
            )

    if role == "teacher":
        if not re.match(TEACHER_REGEX, email):
            raise HTTPException(
                status_code=400,
                detail="Teacher email must be @banasthali.in (not btbt)"
            )

    # -------- ONLY VALID EMAILS REACH HERE --------
    otp = send_otp(email)

    otp_store[email] = {
        "otp": int(otp),
        "expires": datetime.utcnow() + timedelta(minutes=5)
    }

    return {"message": "OTP sent successfully"}


# ---------------- VERIFY OTP ----------------
@router.post("/verify-otp")
def verify_otp(data: dict):
    email = data.get("email")
    otp = data.get("otp")

    if not email or not otp:
        raise HTTPException(status_code=400, detail="Email and OTP required")

    record = otp_store.get(email)

    if not record:
        raise HTTPException(status_code=400, detail="OTP not found")

    if datetime.utcnow() > record["expires"]:
        raise HTTPException(status_code=400, detail="OTP expired")

    if int(otp) != record["otp"]:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # OTP verified → delete
    del otp_store[email]

    return {"message": "OTP verified successfully"}

# ---------------- REGISTER ----------------

@router.post("/register")
def register_user(data: dict):
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")  

    if not name or not email or not password or not role:
        raise HTTPException(status_code=400, detail="All fields required")

    email = email.lower()

    # -------- ROLE BASED EMAIL VALIDATION --------
    if role == "student":
        if not re.match(STUDENT_REGEX, email):
            raise HTTPException(
                status_code=400,
                detail="Student email must start with btbt and end with @banasthali.in"
            )

    if role == "teacher":
        if not re.match(TEACHER_REGEX, email):
            raise HTTPException(
                status_code=400,
                detail="Teacher email must be @banasthali.in (not btbt)"
            )

    # -------- DUPLICATE CHECK --------
    if users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="User already exists")

    # -------- SAVE USER --------
    users_collection.insert_one({
        "name": name,
        "email": email,
        "password": hash_password(password),
        "role": role,
        "created_at": datetime.utcnow()
    })

    return {"message": "User registered successfully"}


# ---------------- LOGIN ----------------
@router.post("/login")
def login(data: dict):
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")

    user = users_collection.find_one({"email": email.lower()})

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Wrong password")

    token = create_access_token({
        "sub": user["email"],
        "role": user["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# ---------------- CURRENT USER ----------------
@router.get("/me")
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = users_collection.find_one({"email": email.lower()})

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": str(user["_id"]),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role")
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


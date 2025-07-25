from fastapi import APIRouter, Depends, HTTPException, Form
from database import db
from schemas import User, UserProfile, CategoryUpdateRequest
from auth import hash_password, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from uuid import uuid4
from google.cloud.firestore import FieldFilter

router = APIRouter()

# ✅ Register
@router.post("/register")
def register_user(user: User):
    users_ref = db.collection("users").where(filter=FieldFilter("email", "==", user.email)).stream()
    for doc in users_ref:
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = str(uuid4())
    hashed_password = hash_password(user.password)
    user_data = {
        "name": user.name,
        "email": user.email,
        "password": hashed_password,
        "created_at": datetime.utcnow(),
        "profile_image": None,
        "selected_categories": [],
        "favourites": []
    }
    db.collection("users").document(user.email).set(user_data)
    return {"message": "User registered successfully", "user_id": user_id}


# ✅ Login
@router.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user_email = form_data.username
    users_ref = db.collection("users").where(filter=FieldFilter("email", "==", user_email)).stream()
    user_doc = None
    for doc in users_ref:
        user_doc = doc.to_dict()
        break

    if not user_doc or not verify_password(form_data.password, user_doc["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = create_access_token(data={"sub": user_doc["email"]}, expires_delta=timedelta(days=7))
    return {"access_token": access_token, "token_type": "bearer"}


# ✅ Get Profile
@router.get("/profile", response_model=UserProfile)
def get_user_profile(user_email: str = Depends(get_current_user)):
    user_ref = db.collection("users").document(user_email)
    doc = user_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user = doc.to_dict()
    return {
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
        "profile_image": user.get("profile_image"),
        "selected_categories": user.get("selected_categories", []),
        "favourites": user.get("favourites", [])
    }


# ✅ Update Profile (Name + Cloudinary Image URL)
@router.put("/profile")
def update_user_profile(
    name: str = Form(None),
    profile_image: str = Form(None),  # 🔄 URL string (e.g. from Cloudinary)
    user_email: str = Depends(get_current_user),
):
    user_ref = db.collection("users").document(user_email)
    user_doc = user_ref.get()

    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    updates = {}

    if name:
        updates["name"] = name

    if profile_image:
        updates["profile_image"] = profile_image  # ✅ Save Cloudinary URL

    if updates:
        updates["updated_at"] = datetime.utcnow()
        user_ref.update(updates)

    updated_user = user_ref.get().to_dict()

    return {
        "message": "Profile updated successfully",
        "updated_data": {
            "name": updated_user.get("name"),
            "profile_image": updated_user.get("profile_image")
        }
    }


# ✅ Get All Categories
@router.get("/categories/all", response_model=list[str])
def get_all_categories():
    categories_ref = db.collection("categories").stream()
    return [doc.to_dict()["name"] for doc in categories_ref]


# ✅ Get User Categories
@router.get("/categories", response_model=list[str])
def get_user_categories(user_email: str = Depends(get_current_user)):
    user_ref = db.collection("users").document(user_email)
    doc = user_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user_data = doc.to_dict()
    return user_data.get("selected_categories", [])


# ✅ Update Selected Categories
@router.put("/categories")
def update_user_categories(data: CategoryUpdateRequest, user_email: str = Depends(get_current_user)):
    global_categories = [doc.to_dict()["name"] for doc in db.collection("categories").stream()]
    invalid = [cat for cat in data.selected_categories if cat not in global_categories]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid categories: {invalid}")

    db.collection("users").document(user_email).update({
        "selected_categories": data.selected_categories
    })
    return {"message": "Selected categories updated successfully"}

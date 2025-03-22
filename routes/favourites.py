from fastapi import APIRouter, Depends, HTTPException
from database import db
from auth import get_current_user
from schemas import BlogResponse

router = APIRouter()

# ✅ Add Blog to Favourites
@router.post("/favourites/{blog_id}")
def add_to_favourites(blog_id: str, user_email: str = Depends(get_current_user)):
    user_ref = db.collection("users").document(user_email)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user_doc.to_dict()
    favourites = user_data.get("favourites", [])

    if blog_id in favourites:
        raise HTTPException(status_code=400, detail="Blog already in favourites")

    favourites.append(blog_id)
    user_ref.update({"favourites": favourites})
    return {"message": "Blog added to favourites"}

# ✅ Remove Blog from Favourites
@router.delete("/favourites/{blog_id}")
def remove_from_favourites(blog_id: str, user_email: str = Depends(get_current_user)):
    user_ref = db.collection("users").document(user_email)
    user_doc = user_ref.get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = user_doc.to_dict()
    favourites = user_data.get("favourites", [])

    if blog_id not in favourites:
        raise HTTPException(status_code=404, detail="Blog not in favourites")

    favourites.remove(blog_id)
    user_ref.update({"favourites": favourites})
    return {"message": "Blog removed from favourites"}

# ✅ Get All Favourite Blogs
@router.get("/favourites", response_model=list[BlogResponse])
def get_favourites(user_email: str = Depends(get_current_user)):
    user_doc = db.collection("users").document(user_email).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    favourites = user_doc.to_dict().get("favourites", [])
    blogs = []

    for blog_id in favourites:
        blog_ref = db.collection("blogs").document(blog_id).get()
        if blog_ref.exists:
            blogs.append({"id": blog_ref.id, **blog_ref.to_dict()})

    return blogs

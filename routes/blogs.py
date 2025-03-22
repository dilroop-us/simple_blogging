from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from database import db
from schemas import Blog, BlogUpdate, BlogResponse
from auth import get_current_user
from datetime import datetime
from uuid import uuid4
import os
from typing import Optional

router = APIRouter()
UPLOAD_FOLDER = "uploads/blogs/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ✅ Get All Blogs
@router.get("/", response_model=list[BlogResponse])
def get_all_blogs():
    blogs_ref = db.collection("blogs").stream()
    return [{"id": blog.id, **blog.to_dict()} for blog in blogs_ref]


# ✅ Get Blogs by Selected Categories
@router.get("/by-selected-categories", response_model=list[BlogResponse])
def get_blogs_by_selected_categories(user_email: str = Depends(get_current_user)):
    user_doc = db.collection("users").document(user_email).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    selected_categories = user_doc.to_dict().get("selected_categories", [])
    if not selected_categories:
        return []

    blogs_ref = db.collection("blogs").stream()
    return [
        {"id": blog.id, **blog.to_dict()}
        for blog in blogs_ref
        if blog.to_dict().get("category") in selected_categories
    ]


# ✅ Get My Blogs
@router.get("/my-blogs", response_model=list[BlogResponse])
def get_my_blogs(user_email: str = Depends(get_current_user)):
    blogs_ref = db.collection("blogs").where("author_email", "==", user_email).stream()
    return [{"id": blog.id, **blog.to_dict()} for blog in blogs_ref]


# ✅ Create Blog
@router.post("/", response_model=dict)
def create_blog(
    category: str = Form(...),
    topic: str = Form(...),
    title: str = Form(...),
    readTime: str = Form(...),
    content: str = Form(...),
    image: UploadFile = File(None),
    user_email: str = Depends(get_current_user)
):
    blog_id = str(uuid4())

    user_doc = db.collection("users").document(user_email).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_doc.to_dict()

    blog_data = {
        "category": category,
        "topic": topic,
        "title": title,
        "readTime": readTime,
        "content": content,
        "author": user.get("name", user_email),
        "author_email": user_email,
        "avatar": user.get("profile_image"),
        "created_at": datetime.utcnow(),
        "updated_at": None
    }

    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{blog_id}.{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(image_path, "wb") as f:
            f.write(image.file.read())
        blog_data["imageUrl"] = image_path

    db.collection("blogs").document(blog_id).set(blog_data)
    return {"message": "Blog created successfully", "blog_id": blog_id}


# ✅ Get Blog by ID
@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog_by_id(blog_id: str):
    blog_ref = db.collection("blogs").document(blog_id)
    blog_doc = blog_ref.get()
    if not blog_doc.exists:
        raise HTTPException(status_code=404, detail="Blog not found")
    return {"id": blog_doc.id, **blog_doc.to_dict()}


# ✅ PUT Update
@router.put("/{blog_id}")
def update_blog_put(
    blog_id: str,
    category: str = Form(...),
    topic: str = Form(...),
    title: str = Form(...),
    readTime: str = Form(...),
    content: str = Form(...),
    image: UploadFile = File(None),
    user_email: str = Depends(get_current_user)
):
    blog_ref = db.collection("blogs").document(blog_id)
    existing = blog_ref.get()
    if not existing.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    blog_data = existing.to_dict()
    if blog_data.get("author_email") != user_email:
        raise HTTPException(status_code=403, detail="Permission denied")

    updated_data = {
        "category": category,
        "topic": topic,
        "title": title,
        "readTime": readTime,
        "content": content,
        "author": blog_data.get("author"),
        "author_email": blog_data.get("author_email"),
        "avatar": blog_data.get("avatar"),
        "created_at": blog_data.get("created_at"),
        "updated_at": datetime.utcnow(),
    }

    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{blog_id}.{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(image_path, "wb") as f:
            f.write(image.file.read())
        updated_data["imageUrl"] = image_path
    else:
        updated_data["imageUrl"] = blog_data.get("imageUrl")

    blog_ref.set(updated_data)
    return {"message": "Blog updated successfully (PUT)"}


# ✅ PATCH Update
@router.patch("/{blog_id}")
def update_blog_patch(
    blog_id: str,
    category: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    readTime: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    image: UploadFile = File(None),
    user_email: str = Depends(get_current_user)
):
    blog_ref = db.collection("blogs").document(blog_id)
    existing = blog_ref.get()
    if not existing.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    blog_data = existing.to_dict()
    if blog_data.get("author_email") != user_email:
        raise HTTPException(status_code=403, detail="Permission denied")

    updates = {"updated_at": datetime.utcnow()}

    if category: updates["category"] = category
    if topic: updates["topic"] = topic
    if title: updates["title"] = title
    if readTime: updates["readTime"] = readTime
    if content: updates["content"] = content

    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{blog_id}.{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(image_path, "wb") as f:
            f.write(image.file.read())
        updates["imageUrl"] = image_path

    blog_ref.update(updates)
    return {"message": "Blog updated successfully (PATCH)"}


# ✅ Delete Blog
@router.delete("/{blog_id}")
def delete_blog(blog_id: str, user_email: str = Depends(get_current_user)):
    blog_ref = db.collection("blogs").document(blog_id)
    blog = blog_ref.get()
    if not blog.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    if blog.to_dict().get("author_email") != user_email:
        raise HTTPException(status_code=403, detail="Permission denied")

    blog_ref.delete()
    return {"message": "Blog deleted successfully"}

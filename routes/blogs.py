from fastapi import APIRouter, Depends, HTTPException, Form, Query
from database import db
from schemas import BlogResponse
from auth import get_current_user
from datetime import datetime
from uuid import uuid4
from typing import Optional
from google.cloud import firestore

router = APIRouter()

# ✅ Get All Blogs
@router.get("/", response_model=list[BlogResponse])
def get_all_blogs(
    category: Optional[list[str]] = Query(None),
    page: int = Query(1, ge=1)
):
    blogs_ref = db.collection("blogs").order_by("created_at", direction=firestore.Query.DESCENDING).stream()
    blogs = [
        {"id": blog.id, **blog.to_dict()}
        for blog in blogs_ref
        if not category or blog.to_dict().get("category") in category
    ]
    start = (page - 1) * 10
    return blogs[start:start + 10]

# ✅ Search Blogs (Paginated & Sorted)
@router.get("/search", response_model=list[BlogResponse])
def search_blogs(
    query: str = Query(...),
    page: int = Query(1, ge=1)
):
    all_blogs = list(db.collection("blogs").order_by("created_at", direction=firestore.Query.DESCENDING).stream())
    matched = [
        {"id": blog.id, **blog.to_dict()}
        for blog in all_blogs
        if query.lower() in blog.to_dict().get("title", "").lower()
        or query.lower() in blog.to_dict().get("topic", "").lower()
        or query.lower() in blog.to_dict().get("content", "").lower()
        or query.lower() in blog.to_dict().get("category", "").lower()
    ]
    start = (page - 1) * 10
    return matched[start:start + 10]


# ✅ Blogs by Selected Categories
@router.get("/by-selected-categories", response_model=list[BlogResponse])
def get_blogs_by_selected_categories(
    user_email: str = Depends(get_current_user),
    category: Optional[list[str]] = Query(None),
    page: int = Query(1, ge=1)
):
    user_doc = db.collection("users").document(user_email).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    selected_categories = user_doc.to_dict().get("selected_categories", [])
    blogs_ref = db.collection("blogs").order_by("created_at", direction=firestore.Query.DESCENDING).stream()

    filtered = [
        {"id": blog.id, **blog.to_dict()}
        for blog in blogs_ref
        if blog.to_dict().get("category") in selected_categories and
           (not category or blog.to_dict().get("category") in category)
    ]
    start = (page - 1) * 10
    return filtered[start:start + 10]


# ✅ My Blogs
@router.get("/my-blogs", response_model=list[BlogResponse])
def get_my_blogs(
    user_email: str = Depends(get_current_user),
    page: int = Query(1, ge=1)
):
    blogs_ref = db.collection("blogs") \
        .where("author_email", "==", user_email) \
        .order_by("created_at", direction=firestore.Query.DESCENDING) \
        .stream()
    blogs = [{"id": blog.id, **blog.to_dict()} for blog in blogs_ref]
    start = (page - 1) * 10
    return blogs[start:start + 10]


# ✅ Create Blog
@router.post("/", response_model=dict)
def create_blog(
    category: str = Form(...),
    topic: str = Form(...),
    title: str = Form(...),
    readTime: str = Form(...),
    content: str = Form(...),
    image_url: Optional[str] = Form(None),  # 🔄 Cloudinary URL from frontend
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
        "updated_at": None,
        "imageUrl": image_url
    }

    db.collection("blogs").document(blog_id).set(blog_data)
    return {"message": "Blog created successfully", "blog_id": blog_id}

# ✅ Get Blog by ID
@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog_by_id(blog_id: str):
    blog_doc = db.collection("blogs").document(blog_id).get()
    if not blog_doc.exists:
        raise HTTPException(status_code=404, detail="Blog not found")
    return {"id": blog_doc.id, **blog_doc.to_dict()}

# ✅ Update Blog (PUT)
@router.put("/{blog_id}")
def update_blog_put(
    blog_id: str,
    category: str = Form(...),
    topic: str = Form(...),
    title: str = Form(...),
    readTime: str = Form(...),
    content: str = Form(...),
    image_url: Optional[str] = Form(None),  # 🔄 URL from frontend
    user_email: str = Depends(get_current_user)
):
    blog_ref = db.collection("blogs").document(blog_id)
    existing = blog_ref.get()
    if not existing.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    blog_data = existing.to_dict()
    if blog_data["author_email"] != user_email:
        raise HTTPException(status_code=403, detail="Permission denied")

    updated_data = {
        "category": category,
        "topic": topic,
        "title": title,
        "readTime": readTime,
        "content": content,
        "author": blog_data["author"],
        "author_email": blog_data["author_email"],
        "avatar": blog_data.get("avatar"),
        "created_at": blog_data["created_at"],
        "updated_at": datetime.utcnow(),
        "imageUrl": image_url if image_url else blog_data.get("imageUrl")
    }

    blog_ref.set(updated_data)
    return {"message": "Blog updated successfully (PUT)"}

# ✅ Partial Update (PATCH)
@router.patch("/{blog_id}")
def update_blog_patch(
    blog_id: str,
    category: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    readTime: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),  # 🔄 Cloudinary URL
    user_email: str = Depends(get_current_user)
):
    blog_ref = db.collection("blogs").document(blog_id)
    existing = blog_ref.get()
    if not existing.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    blog_data = existing.to_dict()
    if blog_data["author_email"] != user_email:
        raise HTTPException(status_code=403, detail="Permission denied")

    updates = {"updated_at": datetime.utcnow()}

    if category: updates["category"] = category
    if topic: updates["topic"] = topic
    if title: updates["title"] = title
    if readTime: updates["readTime"] = readTime
    if content: updates["content"] = content
    if image_url: updates["imageUrl"] = image_url

    blog_ref.update(updates)
    return {"message": "Blog updated successfully (PATCH)"}

# ✅ Delete Blog
@router.delete("/{blog_id}")
def delete_blog(blog_id: str, user_email: str = Depends(get_current_user)):
    blog_ref = db.collection("blogs").document(blog_id)
    blog_doc = blog_ref.get()
    if not blog_doc.exists:
        raise HTTPException(status_code=404, detail="Blog not found")
    if blog_doc.to_dict()["author_email"] != user_email:
        raise HTTPException(status_code=403, detail="Permission denied")
    blog_ref.delete()
    return {"message": "Blog deleted successfully"}

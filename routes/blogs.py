from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from database import db
from schemas import Blog, BlogUpdate, BlogResponse
from auth import get_current_user
from datetime import datetime
from uuid import uuid4
import os

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

# ✅ Get Current User's Blogs
@router.get("/my-blogs", response_model=list[BlogResponse])
def get_my_blogs(user_email: str = Depends(get_current_user)):
    blogs_ref = db.collection("blogs").where("author", "==", user_email).stream()
    return [{"id": blog.id, **blog.to_dict()} for blog in blogs_ref]

# ✅ Create Blog with Image Upload
@router.post("/", response_model=dict)
def create_blog(
    blog: Blog = Depends(),
    image: UploadFile = File(None),
    user_email: str = Depends(get_current_user)
):
    blog_id = str(uuid4())
    blog_data = blog.dict()

    # Get user info
    user_doc = db.collection("users").document(user_email).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    user = user_doc.to_dict()

    # Auto-fill author & avatar
    blog_data["author"] = user.get("name", user_email)
    blog_data["avatar"] = user.get("profile_image")
    blog_data["created_at"] = datetime.utcnow()
    blog_data["updated_at"] = None

    # Save blog image
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{blog_id}.{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(image_path, "wb") as f:
            f.write(image.file.read())
        blog_data["imageUrl"] = image_path

    db.collection("blogs").document(blog_id).set(blog_data)
    return {"message": "Blog created successfully", "blog_id": blog_id}

@router.get("/{blog_id}", response_model=BlogResponse)
def get_blog_by_id(blog_id: str):
    blog_ref = db.collection("blogs").document(blog_id)
    blog_doc = blog_ref.get()

    if not blog_doc.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    blog_data = blog_doc.to_dict()
    return {"id": blog_doc.id, **blog_data}


# ✅ Update Blog (PUT = full update)
@router.put("/{blog_id}")
def update_blog_put(
    blog_id: str,
    blog: Blog = Depends(),
    image: UploadFile = File(None),
    user_email: str = Depends(get_current_user)
):
    blog_ref = db.collection("blogs").document(blog_id)
    existing = blog_ref.get()
    if not existing.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    if existing.to_dict().get("author") != user_email:
        raise HTTPException(status_code=403, detail="Permission denied")

    blog_data = blog.dict()
    blog_data["created_at"] = existing.to_dict().get("created_at", datetime.utcnow())
    blog_data["updated_at"] = datetime.utcnow()

    # Save updated image if provided
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{blog_id}.{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(image_path, "wb") as f:
            f.write(image.file.read())
        blog_data["imageUrl"] = image_path
    else:
        blog_data["imageUrl"] = existing.to_dict().get("imageUrl")

    blog_ref.set(blog_data)
    return {"message": "Blog updated successfully (PUT)"}

# ✅ Update Blog (PATCH = partial update)
@router.patch("/{blog_id}")
def update_blog_patch(
    blog_id: str,
    blog: BlogUpdate = Depends(),
    image: UploadFile = File(None),
    user_email: str = Depends(get_current_user)
):
    blog_ref = db.collection("blogs").document(blog_id)
    existing = blog_ref.get()
    if not existing.exists:
        raise HTTPException(status_code=404, detail="Blog not found")

    blog_data = existing.to_dict()
    if blog_data.get("author") != user_email:
        raise HTTPException(status_code=403, detail="Permission denied")

    updates = blog.dict(exclude_unset=True)
    updates["updated_at"] = datetime.utcnow()

    # Optional image update
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

    if blog.to_dict().get("author") != user_email:
        raise HTTPException(status_code=403, detail="Permission denied")

    blog_ref.delete()
    return {"message": "Blog deleted successfully"}

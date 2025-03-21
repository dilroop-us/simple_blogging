from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# 🔹 USER SCHEMAS

class User(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserProfile(BaseModel):
    name: str
    email: EmailStr
    created_at: datetime
    profile_image: Optional[str] = None
    selected_categories: List[str] = []

class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_image: Optional[str] = None

class CategoryUpdateRequest(BaseModel):
    selected_categories: List[str]

# 🔹 BLOG SCHEMAS

class Blog(BaseModel):
    author: Optional[str] = None         # Will be auto-set
    category: str
    topic: str
    title: str
    readTime: str                         # e.g., "5 min"
    avatar: Optional[str] = None          # Author profile image
    imageUrl: Optional[str] = None        # Blog image
    content: str

class BlogUpdate(BaseModel):
    category: Optional[str] = None
    topic: Optional[str] = None
    title: Optional[str] = None
    readTime: Optional[str] = None
    avatar: Optional[str] = None
    imageUrl: Optional[str] = None
    content: Optional[str] = None

class BlogResponse(Blog):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

class BlogListResponse(BaseModel):
    blogs: List[BlogResponse]

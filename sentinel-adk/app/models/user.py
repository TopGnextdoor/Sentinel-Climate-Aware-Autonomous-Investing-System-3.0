import uuid
import hashlib
import secrets
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict

# schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str

from app.utils.security import hash_password, verify_password

class UserInDB(BaseModel):
    id: str
    username: str
    email: str
    password_hash: str
    role: str

# In-memory dictionary for MVP
fake_users_db: Dict[str, UserInDB] = {}

def get_user_by_email(email: str) -> Optional[UserInDB]:
    """Retrieves a user by email."""
    for user in fake_users_db.values():
        if user.email == email:
            return user
    return None

def create_user(user_data: UserCreate) -> UserResponse:
    """Creates a new user ensuring the email is unique."""
    if get_user_by_email(user_data.email):
        raise ValueError("Email already formally registered.")
        
    user_id = str(uuid.uuid4())
    pass_hash = hash_password(user_data.password)
    
    new_user = UserInDB(
        id=user_id,
        username=user_data.username,
        email=user_data.email,
        password_hash=pass_hash,
        role="Institutional Sentinel"
    )
    
    # Store in mock DB
    fake_users_db[user_id] = new_user
    
    return UserResponse(id=user_id, username=user_data.username, email=user_data.email, role="Institutional Sentinel")

from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None      
    deadline: Optional[str] = None          
    category: Optional[str] = None          

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[str] = None
    category: Optional[str] = None
    completed: bool
    owner_id: int

    class Config:
        from_attributes = True  
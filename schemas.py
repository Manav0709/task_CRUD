from pydantic import BaseModel, Field
from typing import List, Literal


class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    fullname: str | None = None


class TaskBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    tags: List[str] = []


class TaskCreate(TaskBase):
    owner : User

class Task(TaskBase):
    id: int
    owner: User

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "title": "Learn FastAPI",
                "description": "Build async CRUD app",
                "priority": "high",
                "tags": ["backend", "api"],
                "owner": {"username": "manav", "full_name": "Manav Sharma"},
            }
        }
    }

class TaskFilter(BaseModel):
    limit : int = Field(10,gt=0,le=50)
    offset : int = Field(0,ge=0)
    priority : Literal["low","medium","high"] | None = None
    

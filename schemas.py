from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Literal


class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    fullname: str | None = None

    @field_validator("username")
    @classmethod
    def username_no_spaces(cls, v):
        if " " in v:
            raise ValueError("Username cannot contain spaces")
        return v.lower()


class TaskBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=100)
    description: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    tags: List[str] = []

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, v):
        if v is None:
            return []
        return [tag.lower() for tag in v]

    @model_validator(mode="after")
    def check_high_priority(self):
        if self.priority == "high" and not self.description:
            raise ValueError("High Priority tasks must have a description")
        return self


class TaskCreate(TaskBase):
    owner: User


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
    limit: int = Field(10, gt=0, le=50)
    offset: int = Field(0, ge=0)
    priority: Literal["low", "medium", "high"] | None = None

from datetime import timedelta
from typing import List, Annotated

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, HTTPException, Query, Path, Depends, status

from schemas import Task, TaskCreate, TaskFilter, Token
from database import tasks_db, users_db
from auth import (
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
)


app = FastAPI(title="Async Task CRUD API")


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:

    user = authenticate_user(users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.post("/tasks/", response_model=Task)
async def create_task(task: TaskCreate, user=Depends(get_current_user)):
    task_id = len(tasks_db) + 1
    new_task = Task(id=task_id, owner=user, **task.model_dump())
    tasks_db.append(new_task)
    return new_task


@app.get("/tasks", response_model=List[Task])
async def read_tasks(
    filters: Annotated[TaskFilter, Query()], user=Depends(get_current_user)
):
    results = tasks_db[filters.offset : filters.offset + filters.limit]

    if filters.priority:
        results = [t for t in results if t.priority == filters.priority]
    return results


@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(
    task_id: Annotated[int, Path(ge=1)], user=Depends(get_current_user)
):
    for task in tasks_db:
        if task.id == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: int, updated_task: TaskCreate, user=Depends(get_current_user)
):
    for index, task in enumerate(tasks_db):
        if task.id == task_id:
            new_task = Task(id=task_id, owner=task.owner, **updated_task.model_dump())
            tasks_db[index] = new_task
            return new_task
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, user=Depends(get_current_user)):
    for index, task in enumerate(tasks_db):
        if task.id == task_id:
            tasks_db.pop(index)
            return {"message": "Task Deleted"}
    raise HTTPException(status_code=404, detail="Task not found")

from fastapi import FastAPI, HTTPException, Query, Path
from typing import List, Annotated
from schemas import Task, TaskCreate, TaskFilter
from database import tasks_db

app = FastAPI(title="Async Task CRUD API")


@app.post("/tasks/", response_model=Task)
async def create_task(task: TaskCreate):
    task_id = len(tasks_db) + 1
    new_task = Task(id=task_id, **task.model_dump())
    tasks_db.append(new_task)
    return new_task


@app.get("/tasks", response_model=List[Task])
async def read_tasks(filters: Annotated[TaskFilter, Query()]):
    results = tasks_db[filters.offset : filters.offset + filters.limit]

    if filters.priority:
        results = [t for t in results if t.priority == filters.priority]
    return results


@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(task_id: Annotated[int, Path(ge=1)]):
    for task in tasks_db:
        if task.id == task_id:
            return task
        raise HTTPException(status_code=404, detail="Task not found")


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, updated_task: TaskCreate):
    for index, task in enumerate(tasks_db):
        if task.id == task_id:
            new_task = Task(id=task_id, **updated_task.model_dump())
            tasks_db[index] = new_task
            return new_task
        raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    for index, task in enumerate(tasks_db):
        if task.id == task_id:
            tasks_db.pop(index)
            return {"message": "Task Deleted"}
        raise HTTPException(status_code=404, detail="Task not found")

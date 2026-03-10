from datetime import timedelta
from typing import List, Annotated

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import FastAPI, HTTPException, Query, Path, Depends, status

from schemas import Task, TaskCreate, TaskFilter, Token, User
from database import init_db, get_connection
from auth import (
    authenticate_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    get_password_hash,
)


app = FastAPI(title="Async Task CRUD API")


@app.on_event("startup")
def startup():
    init_db()


@app.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:

    user = authenticate_user(form_data.username, form_data.password)
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


@app.post("/register")
async def register_user(user: User, password: str):

    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = get_password_hash(password)

    try:
        cursor.execute(
            """
            INSERT INTO users (username, fullname, hashed_password)
            VALUES (?, ?, ?)
            """,
            (user.username, user.fullname, hashed_password),
        )
        conn.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="User already exists")

    conn.close()

    return {"message": "User created successfully"}


@app.post("/tasks/", response_model=Task)
async def create_task(task: TaskCreate, user=Depends(get_current_user)):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (title, description, priority, tags, owner)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            task.title,
            task.description,
            task.priority,
            ",".join(task.tags),
            user.username,
        ),
    )

    conn.commit()

    task_id = cursor.lastrowid
    conn.close()

    return Task(id=task_id, owner=user, **task.model_dump())


@app.get("/tasks", response_model=List[Task])
async def read_tasks(
    filters: Annotated[TaskFilter, Query()], user=Depends(get_current_user)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks LIMIT ? OFFSET ?", (filters.limit, filters.offset)
    )

    rows = cursor.fetchall()
    conn.close()

    results = []

    for row in rows:
        results.append(
            Task(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                priority=row["priority"],
                tags=row["tags"].split(",") if row["tags"] else [],
                owner={"username": row["owner"], "fullname": None},
            )
        )

    if filters.priority:
        results = [t for t in results if t.priority == filters.priority]

    return results


@app.get("/tasks/{task_id}", response_model=Task)
async def read_task(
    task_id: Annotated[int, Path(ge=1)], user=Depends(get_current_user)
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()

    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Task not found")

    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        priority=row["priority"],
        tags=row["tags"].split(",") if row["tags"] else [],
        owner={"username": row["owner"], "fullname": None},
    )


from database import get_connection


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: int, updated_task: TaskCreate, user=Depends(get_current_user)
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET title = ?, description = ?, priority = ?, tags = ?
        WHERE id = ?
        """,
        (
            updated_task.title,
            updated_task.description,
            updated_task.priority,
            ",".join(updated_task.tags),
            task_id,
        ),
    )

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    conn.commit()
    conn.close()

    return Task(id=task_id, owner=user, **updated_task.model_dump())


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, user=Depends(get_current_user)):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,),
    )

    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    conn.commit()
    conn.close()

    return {"message": "Task Deleted"}

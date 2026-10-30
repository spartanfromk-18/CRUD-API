import sqlite3
from typing import Optional
from fastapi import FastAPI, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Task API - SQLite Backend",
    version="2.0",
    description="Persistent CRUD API backed by SQLite."
)

DB_FILE = "tasks.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Enables column access by name
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        # Seed 3 tasks only if table is empty
        cursor = conn.execute("SELECT COUNT(*) FROM tasks")
        count = cursor.fetchone()[0]
        if count == 0:
            initial_tasks = [
                ("Complete FastAPI CRUD assignment", 0),
                ("Test endpoints with curl", 1),
                ("Verify SQLite persistence", 0),
            ]
            conn.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", initial_tasks)
            conn.commit()

# Initialize database and seed data on startup
init_db()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"error": "Invalid request body"})

class TaskCreate(BaseModel):
    title: Optional[str] = Field(default=None, examples=["Buy milk"])

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, examples=["Buy organic milk"])
    done: Optional[bool] = Field(default=None, examples=[True])

@app.get("/", summary="API Info")
def get_api_info():
    return {"name": "Task API", "version": "2.0", "storage": "SQLite"}

@app.get("/health", summary="Health check")
def health_check():
    return {"status": "ok"}

@app.get("/tasks", summary="List tasks with optional filtering and search")
def list_tasks(
    done: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None)
):
    with get_db() as conn:
        query = "SELECT id, title, done FROM tasks"
        params = []
        conditions = []

        if done is not None:
            conditions.append("done = ?")
            params.append(1 if done else 0)
        if search is not None:
            conditions.append("title LIKE ?")
            params.append(f"%{search.strip()}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return [{"id": row["id"], "title": row["title"], "done": bool(row["done"])} for row in rows]

@app.get("/tasks/{task_id}", summary="Get a single task by ID")
def get_task(task_id: int):
    with get_db() as conn:
        cursor = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(payload: TaskCreate):
    if payload.title is None or not payload.title.strip():
        return JSONResponse(status_code=400, content={"error": "Field 'title' is required and cannot be empty"})
    
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (payload.title.strip(), 0)
        )
        conn.commit()
        new_id = cursor.lastrowid
        return {"id": new_id, "title": payload.title.strip(), "done": False}

@app.put("/tasks/{task_id}", summary="Update an existing task")
def update_task(task_id: int, payload: TaskUpdate):
    with get_db() as conn:
        cursor = conn.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if not row:
            return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
        
        if payload.title is None and payload.done is None:
            return JSONResponse(status_code=400, content={"error": "Request body must provide 'title' and/or 'done'"})
        
        current_title = row["title"]
        current_done = row["done"]

        if payload.title is not None:
            if not payload.title.strip():
                return JSONResponse(status_code=400, content={"error": "Field 'title' cannot be empty"})
            current_title = payload.title.strip()
        
        if payload.done is not None:
            current_done = 1 if payload.done else 0

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (current_title, current_done, task_id)
        )
        conn.commit()
        return {"id": task_id, "title": current_title, "done": bool(current_done)}

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    with get_db() as conn:
        cursor = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if not cursor.fetchone():
            return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
        
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return Response(status_code=204)

@app.get("/stats", summary="Task stats")
def get_stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
        return {"total": total, "done": done, "open": total - done}
import os
import psycopg
from psycopg.rows import dict_row
from typing import Optional
from fastapi import FastAPI, Query, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Task API - PostgreSQL Backend",
    version="3.0",
    description="Persistent CRUD API backed by PostgreSQL and Docker."
)

DATABASE_URL = os.getenv("DATABASE_URL", "postgres://postgres:dev@localhost:5432/tasks")

def get_db():
    # Connect using psycopg 3 with dict rows for easy JSON serialization
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT FALSE
            )
        """)
        # Seed 3 tasks only if table is empty
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM tasks")
            count = cur.fetchone()["count"]
            if count == 0:
                initial_tasks = [
                    ("Complete FastAPI PostgreSQL assignment", False),
                    ("Test endpoints with curl", True),
                    ("Verify Docker Compose persistence", False),
                ]
                for title, done in initial_tasks:
                    cur.execute("INSERT INTO tasks (title, done) VALUES (%s, %s)", (title, done))
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
    return {"name": "Task API", "version": "3.0", "storage": "PostgreSQL"}

@app.get("/health", summary="Health check")
def health_check():
    return {"status": "ok"}

@app.get("/tasks", summary="List tasks with optional filtering and search")
def list_tasks(
    done: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None)
):
    with get_db() as conn:
        with conn.cursor() as cur:
            query = "SELECT id, title, done FROM tasks"
            params = []
            conditions = []

            if done is not None:
                conditions.append("done = %s")
                params.append(done)
            if search is not None:
                conditions.append("title ILIKE %s")
                params.append(f"%{search.strip()}%")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cur.execute(query, params)
            return cur.fetchall()

@app.get("/tasks/{task_id}", summary="Get a single task by ID")
def get_task(task_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
            row = cur.fetchone()
            if not row:
                return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
            return row

@app.post("/tasks", status_code=201, summary="Create a new task")
def create_task(payload: TaskCreate):
    if payload.title is None or not payload.title.strip():
        return JSONResponse(status_code=400, content={"error": "Field 'title' is required and cannot be empty"})
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING id, title, done",
                (payload.title.strip(), False)
            )
            conn.commit()
            return cur.fetchone()

@app.put("/tasks/{task_id}", summary="Update an existing task")
def update_task(task_id: int, payload: TaskUpdate):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
            row = cur.fetchone()
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
                current_done = payload.done

            cur.execute(
                "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING id, title, done",
                (current_title, current_done, task_id)
            )
            conn.commit()
            return cur.fetchone()

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete a task")
def delete_task(task_id: int):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
            if not cur.fetchone():
                return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
            
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            conn.commit()
            return Response(status_code=204)

@app.get("/stats", summary="Task stats")
def get_stats():
    with get_db() as conn:
        with conn.cursor() as cur:
            total = cur.execute("SELECT COUNT(*) FROM tasks").fetchone()["count"]
            done = cur.execute("SELECT COUNT(*) FROM tasks WHERE done = TRUE").fetchone()["count"]
            return {"total": total, "done": done, "open": total - done}
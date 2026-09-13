import sqlite3
import pandas as pd
import os
from pathlib import Path
from pydantic import BaseModel
import duckdb

from fastapi import FastAPI, UploadFile,File, Form, HTTPException, Depends
from fastapi import BackgroundTasks
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
# from langchain_community.embeddings.openai import OpenAIEmbeddings
# from dotenv import load_dotenv
from passlib.hash import bcrypt
# from langchain_core.documents import Document

app = FastAPI()
security = HTTPBasic()

# Dummy user database
# users_db: Dict[str, Dict[str, str]] = {
#     "Tony": {"password": "password123", "role": "engineering"},
#     "Bruce": {"password": "securepass", "role": "marketing"},
#     "Sam": {"password": "financepass", "role": "finance"},
#     "Peter": {"password": "pete123", "role": "engineering"},
#     "Sid": {"password": "sidpass123", "role": "marketing"},
#     "Natasha": {"password": "hrpass123", "role": "hr"}
# }


# -------------------------
# === DUCKDB SETUP ===
# -------------------------
# Set path to DuckDB database file
DUCKDB_DIR = Path("static/data")
DUCKDB_DIR.mkdir(parents=True, exist_ok=True)  # ensure directory exists

DUCKDB_PATH = DUCKDB_DIR/"structured_queries.duckdb"

# Connect to DuckDB file (creates file if not exists)
duck_conn = duckdb.connect(str(DUCKDB_PATH))

duck_conn.execute("""
    CREATE TABLE IF NOT EXISTS tables_metadata (
        table_name TEXT,
        role TEXT
    )
""")

# -------------------------
# === SQLITE DATABASE SETUP ===
# -------------------------

conn = sqlite3.connect("roles_docs.db", check_same_thread=False)
c = conn.cursor()
c.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    role TEXT,
    filepath TEXT NOT NULL,
    headers_str TEXT,
    embedded INTEGER DEFAULT 0
);
""")
conn.commit()

def create_default_user():
    conn_local = sqlite3.connect("roles_docs.db")
    c_local = conn_local.cursor()

    c_local.execute("INSERT OR IGNORE INTO roles (role_name) VALUES (?)", ("C-Level",))
    hashed_pw = bcrypt.hash("admin123")
    try:
        c_local.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ("admin", hashed_pw, "C-Level"))
        conn_local.commit()
        print("✅ Default C-Level user created.")
    except sqlite3.IntegrityError:
        print("⚠️ User already exists.")
    conn_local.close()


# Call it on startup
create_default_user()










# Authentication dependency
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password
    print("username: ", username)
    print("password: ", password)
    # user = users_db.get(username)
    c.execute("SELECT password, role FROM users WHERE username = ?", (username,))

    row = c.fetchone()
    print("DB row:", row)
    if not row or not bcrypt.verify(password, row[0]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": username, "role": row[1]}


# === MODELS ===
class ChatRequest(BaseModel):
    question: str

# Login endpoint
@app.get("/login")
def login(user=Depends(authenticate)):
    return {"message": f"Welcome {user['username']}!", "role": user["role"]}



@app.get("/roles")
def get_roles(user=Depends(authenticate)):
    c.execute("SELECT role_name FROM roles")
    roles = [r[0] for r in c.fetchall()]
    return {"roles": roles}




@app.post("/create-user")
def create_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    user=Depends(authenticate)
):
    if user["role"] != "C-Level":
        raise HTTPException(status_code=403, detail="Only C-Level can create users.")

    c.execute("SELECT 1 FROM roles WHERE role_name = ?", (role,))
    if not c.fetchone():
        raise HTTPException(status_code=400, detail="Invalid role")

    hashed = bcrypt.hash(password)
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed, role))
        conn.commit()
        return {"message": f"User '{username}' added with role '{role}'"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="User already exists")

@app.post("/create-role")
def create_role(role_name: str = Form(...), user=Depends(authenticate)):
    if user["role"] != "C-Level":
        raise HTTPException(status_code=403, detail="Only C-Level can create roles.")

    try:
        c.execute("INSERT INTO roles (role_name) VALUES (?)", (role_name,))
        conn.commit()
        return {"message": f"Role '{role_name}' created"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Role already exists")    

@app.get("/my-profile")
def my_profile(user=Depends(authenticate)):

    return {
        "username": user["username"],"role": user["role"]
    }
    




# Protected test endpoint
@app.get("/test")
def test(user=Depends(authenticate)):
    return {"message": f"Hello {user['username']}! You can now chat.", "role": user["role"]}


# Protected chat endpoint
@app.post("/chat")
def query(user=Depends(authenticate), message: str = "Hello"):
    return "Implement this endpoint."



@app.post("/upload-docs")
async def upload_docs(file: UploadFile = File(...), role: str = Form(...)):
    try:
        filename = file.filename
        extension = Path(filename).suffix.lower()

        # Prepare storage
        role_dir = os.path.join(UPLOAD_DIR, role)
        os.makedirs(role_dir, exist_ok=True)
        filepath = os.path.join(role_dir, filename)

        # Read content + save file
        data = await file.read()  # Read once

        with open(filepath, "wb") as f:
            f.write(data)  # Save file for future indexing

        # Convert to string content for validation (optional)
        if extension == ".csv":
            from io import BytesIO
            df = pd.read_csv(BytesIO(data))
            content = df.to_string(index=False)

             # Load for DuckDB
            df1 = pd.read_csv(filepath)
            table_name = Path(filepath).stem.replace("-", "_")

            # Save metadata including headers
            headers = df1.columns.tolist()
            headers_str = ",".join(headers)

            duck_conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df1")

            # ✅ Save metadata to DuckDB tables_metadata
            duck_conn.execute(
                "INSERT INTO tables_metadata (table_name, role) VALUES (?, ?)",
                (table_name, role)
            )

        elif extension == ".md":
            content = data.decode("utf-8")
            headers_str = None  # explicitly set to None
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # Save metadata to DB
        conn = sqlite3.connect("roles_docs.db")
        c = conn.cursor()
        c.execute("INSERT INTO documents (filename, role, filepath,headers_str,embedded) VALUES (?, ?, ?,?,?)",
                  (filename, role, filepath, headers_str,0))
        #doc_id = c.lastrowid  # ✅ Get inserted doc ID
        conn.commit()
        conn.close()
        
        run_indexer()
        print("Files indexed successfully")
        return JSONResponse(content={"message": f"{filename} uploaded successfully for role '{role}'."})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    



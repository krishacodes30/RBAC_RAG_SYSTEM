import os
import re
import sqlite3
from pathlib import Path

import duckdb
from dotenv import load_dotenv
from app.llm.llm_provider import SQL_MODELS
import tabulate

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "roles_docs.db"
DUCKDB_FILE = BASE_DIR / "static" / "data" / "structured_queries.duckdb"

duck_conn = duckdb.connect(str(DUCKDB_FILE))
MODEL_LIST_STR = os.getenv(
    "FREE_GEMINI_MODELS",
    "gemini-2.5-flash,gemini-2.5-flash-lite,gemini-1.5-flash,gemini-1.5-flash-8b"
)
# SQL_MODEL = os.getenv(
#     "SQL_MODEL",
#     "gemini-3.5-flash-lite"
# )

# free_models = ChatGoogleGenerativeAI(
#     model=SQL_MODEL,
#     temperature=0,
#     max_retries=2,
#     google_api_key=GOOGLE_API_KEY
# )
FORBIDDEN = ["insert", "update", "delete", "drop", "alter", "create", "truncate", "replace"]

def get_allowed_tables_for_role(role: str) -> list[str]:
    role = role.lower()
    if role == "c-level":
        query = "SELECT table_name FROM tables_metadata"
        return [row[0] for row in duck_conn.execute(query).fetchall()]
    elif role == "general":
        query = "SELECT table_name FROM tables_metadata WHERE LOWER(role) = 'general'"
        return [row[0] for row in duck_conn.execute(query).fetchall()]
    else:
        query = "SELECT table_name FROM tables_metadata WHERE LOWER(role) = ? OR LOWER(role) = 'general'"
        return [row[0] for row in duck_conn.execute(query, [role]).fetchall()]

def extract_tables_from_sql(sql: str) -> list[str]:
    matches = re.findall(r"(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, flags=re.IGNORECASE)
    return list(dict.fromkeys(matches))

def is_safe_query(sql: str) -> bool:
    cleaned_sql = sql.strip().lower().rstrip(";")
    if not cleaned_sql.startswith("select"):
        return False
    for word in FORBIDDEN:
        if re.search(rf"\b{re.escape(word)}\b", cleaned_sql):
            return False
    return True

def get_csv_schemas():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, headers_str, role FROM documents WHERE headers_str IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()

    schemas = []
    for filename, headers_str, role in rows:
        table_name = Path(filename).stem.replace("-", "_")
        columns = headers_str.split(",")
        schemas.append(f"Table: {table_name}\nRole: {role}\nColumns: {', '.join(columns)}")
    return schemas

def translate_nl_to_sql(question: str, allowed_tables: list[str]) -> str:
    schemas = get_csv_schemas()
    allowed_schemas = []
    for schema in schemas:
        table_name = schema.split("\n")[0].replace("Table: ", "")
        if table_name in allowed_tables:
            allowed_schemas.append(schema)

    schema_block = "\n\n".join(allowed_schemas)
    prompt = f"""You convert natural-language questions into safe DuckDB SQL.

The user is allowed to access ONLY these tables:
{schema_block}

Rules:
1. Return ONLY one SQL SELECT query.
2. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE or other modification statements.
3. Use ONLY the tables listed above.
4. Use the exact column names from the schemas.
5. Do not invent tables or columns.
6. The SQL must be compatible with DuckDB.
7. If the question cannot be answered using the available tables, return:
   SELECT 'Cannot answer from available data' AS answer;

User question:
{question}

SQL:"""

    response = None
    for model_instance in SQL_MODELS:
        try:
            response = model_instance.invoke(prompt)
            if response and response.content:
                break
        except Exception:
            continue

    if not response:
        raise Exception("All configured models failed to respond.")

    sql = response.content.strip()
    return re.sub(r"```sql\s*|\s*```", "", sql, flags=re.IGNORECASE).strip()

async def ask_csv(question: str, role: str, username: str, return_sql: bool = False) -> dict:
    try:
        allowed_tables = get_allowed_tables_for_role(role)
        print(f"[SQL] User={username}, Role={role}")
        print(f"[SQL] Allowed tables={allowed_tables}")

        if not allowed_tables:
            return {"answer": "No structured data is available for your role.", "error": True}

        sql = translate_nl_to_sql(question, allowed_tables)
        print(f"[SQL GENERATED]\n{sql}")

        if not is_safe_query(sql):
            return {"answer": "Only safe SELECT queries are allowed.", "error": True}

        referenced_tables = extract_tables_from_sql(sql)
        print(f"[SQL TABLES USED] {referenced_tables}")

        for table in referenced_tables:
            if table not in allowed_tables:
                return {"answer": f"Access denied to table: {table}", "error": True}

        result = duck_conn.execute(sql).fetchall()
        columns = [description[0] for description in duck_conn.description]
        output = [list(row) for row in result]
        markdown_table = tabulate.tabulate(output, headers=columns, tablefmt="github")

        response = {"answer": markdown_table if output else "Query executed, but no results found."}
        if return_sql:
            response["sql"] = sql

        return response

    except Exception as e:
        print(f"[SQL ERROR] {e}")
        return {"answer": f"SQL processing failed: {str(e)}", "error": True}
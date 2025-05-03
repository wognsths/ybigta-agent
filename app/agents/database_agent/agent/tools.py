from typing import Any
from langchain_core.tools import tool
import httpx
from ..core.config import settings
BASE_URL = settings.DATABASE_URL

def request_helper(method: str, endpoint: str, **kwargs) -> Any:
    url = f"{BASE_URL}{endpoint}"
    try:
        with httpx.Client(timeout=5.0) as client:
            if method.lower() == "get":
                response = client.get(url, **kwargs)
            elif method.lower() == "post":
                response = client.post(url, **kwargs)
            else:
                raise ValueError("Unsupported HTTP method")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@tool
def get_database_schema() -> Any:
    """Fetch the full database schema."""
    return request_helper("get", "/db/schema")

@tool
def get_table_list() -> Any:
    """Retrieve a list of all tables in the database."""
    return request_helper("get", "/db/tables")

@tool
def get_table_sample(table_name: str, limit: int = 5) -> Any:
    """Get a sample of rows from a specific table."""
    return request_helper(
        "get",
        f"/db/{table_name}/sample?limit={limit}")

@tool
def run_custom_query(sql_query: str) -> Any:
    """Run a custom SQL query against the database."""
    return request_helper("post", "/db/query", json={"query": sql_query})

@tool
def get_table_uniques(table_name: str, limit: int = 10) -> Any:
    """Get a unique values from a specific table's columns"""
    return request_helper(
        "get",
        f"/db/{table_name}/uniques?limit={limit}"
    )

@tool
def get_table_summary(table_name: str) -> Any:
    """Get a summary from a specific table"""
    return request_helper(
        "get",
        f"/db/{table_name}/summary"
    )
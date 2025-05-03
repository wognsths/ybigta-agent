from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.database_agent.database.database import db, schema_manager

class QueryRequest(BaseModel):
    query: str

router = APIRouter()

@router.post("/query", summary="Run a custom SQL query")
def run_query(request: QueryRequest):
    try:
        result = db.execute_query(request.query)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}
    
@router.get("/{table_name}/samples", summary="Get sample data of a table")
def get_table_sample(table_name: str, limit: int = 5):
    try:
        sample_data = schema_manager.get_table_sample_data(table_name, limit)
        return {"sample_data": sample_data}
    except Exception as e:
        return {"error": str(e)}
    
@router.get("/schema", summary="Get full database schema")
def get_database_schema():
    schema = schema_manager.get_schema()
    return {"schema": schema}

@router.get("/tables", summary="Get list of tables")
def get_table_list():
    tables = schema_manager.get_tables()
    return {"tables": tables}

@router.get("/{table_name}/summary", summary="Get summaries of a table")
def get_table_summary(table_name: str):
    try:
        summaries = schema_manager.get_table_summary(table_name)
        return {f"Summary of table: {table_name}": summaries}
    except Exception as e:
        return {"error": str(e)}
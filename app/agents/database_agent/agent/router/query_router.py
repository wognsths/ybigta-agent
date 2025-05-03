from fastapi import APIRouter
from pydantic import BaseModel
from starlette.responses import JSONResponse

from ..agent import DBAgent, DBAgentResponse

router = APIRouter()

class QueryInput(BaseModel):
    query: str
    session_id: str

@router.post("/query")
async def handle_query(data: QueryInput):
    db_agent = DBAgent()
    res: DBAgentResponse = db_agent.invoke(data.query, data.session_id)
    return JSONResponse({
        "is_task_complete":  res.status == "completed",
        "require_user_input": res.status == "input_required",
        "content":           res.message,
    })
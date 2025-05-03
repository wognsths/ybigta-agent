from typing import Dict, List, Any, Optional, Union, Literal
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str

class NoAuthorizationError(Exception):
    def __init__(self, query: str, message: str = "Forbidden SQL operation attempted."):
        self.query = query
        self.message = message
        super().__init__(f"{message}\nThis query is blocked. Use this query with directly accessing to database: {query}")

class DBAgentResponse(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str
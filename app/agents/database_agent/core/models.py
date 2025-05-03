from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str

class NoAuthorizationError(Exception):
    def __init__(self, query: str, message: str = "Forbidden SQL operation attempted."):
        self.query = query
        self.message = message
        super().__init__(f"{message}\nThis query is blocked. Use this query with directly accessing to database: {query}")
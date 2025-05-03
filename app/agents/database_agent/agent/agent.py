from typing import Any, Dict, List, Optional, Literal, AsyncIterable
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage

from .tools import get_database_schema, get_table_list, get_table_sample, get_table_summary, get_table_uniques, run_custom_query
from .prompts import SYSTEM_INSTRUCTION

class DBAgentResponse(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

memory = MemorySaver()

class DBAgent:
    SYSTEM_INSTRUCTION = SYSTEM_INSTRUCTION
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"))
        self.tools = [
            get_database_schema,
            get_table_list,
            get_table_sample,
            get_table_summary,
            get_table_uniques,
            run_custom_query
        ]
        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=memory,
            prompt=self.SYSTEM_INSTRUCTION,
            response_format=DBAgentResponse
        )
    def invoke(self, query, sessionId) -> DBAgentResponse:
        config = {"configurable": {"thread_id": sessionId}}
        self.graph.invoke({"messages": [("user", query)]}, config)
        sr = self.graph.get_state(config).values.get("structured_response")
        if isinstance(sr, DBAgentResponse):
            return sr

        return DBAgentResponse(
            status="error",
            message="Unexpected error: unable to retrieve agent response."
        )
    
    async def stream(self, query, sessionId) -> AsyncIterable[Dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": f"Calling tool `{message.tool_calls[0]['name']}` with arguments {message.tool_calls[0]['arguments']}"
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": f"Returned result: {message.content}"
                }

        current_state = self.graph.get_state(config)
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(structured_response, DBAgentResponse):
            yield {
                "is_task_complete": True if structured_response.status == "completed" else False,
                "require_user_input": structured_response.status == "input_required",
                "content": structured_response.message,
            }
        else:
            yield {
                "is_task_complete": False,
                "require_user_input": True,
                "content": "We are unable to process your request at the moment. Please try again.",
            }
        yield self.get_agent_response(config)

    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)        
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(structured_response, DBAgentResponse): 
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
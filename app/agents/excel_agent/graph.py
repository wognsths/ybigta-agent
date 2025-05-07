"""LangGraph implementation for the Excel Agent."""

import logging
from typing import Dict, Any, Optional, TypedDict
from io import BytesIO

import pandas as pd
import openpyxl
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field

from langgraph.graph import StateGraph, END
from langgraph.prebuilt.tool_executor import ToolExecutor

from app.agents.excel_agent.tools import (
    load_template_wb,
    transform_df_for_template,
    map_df_to_workbook,
    save_workbook,
)

logger = logging.getLogger(__name__)

class ExcelState(TypedDict):
    """The state of the Excel Agent workflow."""
    df: pd.DataFrame
    context: Dict[str, Any]
    wb: Optional[openpyxl.Workbook]
    file_bytes: Optional[bytes]
    filename: Optional[str]
    error: Optional[str]

class ExcelRequest(BaseModel):
    """Request model for Excel Agent."""
    df: pd.DataFrame
    context: Dict[str, Any] = Field(
        ..., example={"template": "가", "date_range": "2025-04-14/19"}
    )

class ExcelResponse(BaseModel):
    """Response model for Excel Agent."""
    file_bytes: bytes
    filename: str

def get_excel_agent(llm: Optional[BaseChatModel] = None) -> StateGraph:
    """
    Create the Excel Agent workflow graph.
    
    Args:
        llm: Optional language model for advanced functionality
        
    Returns:
        Compiled StateGraph for Excel processing
    """
    # Create tool executor
    tools = [
        load_template_wb,
        transform_df_for_template,
        map_df_to_workbook,
        save_workbook,
    ]
    tool_executor = ToolExecutor(tools)
    
    # Initialize LLM if not provided
    if llm is None:
        try:
            llm = ChatOpenAI(model="gpt-3.5-turbo")
        except Exception as e:
            logger.warning(f"Could not initialize OpenAI LLM: {str(e)}. Some advanced features may be unavailable.")
            llm = None
    
    # Define the graph
    workflow = StateGraph(ExcelState)
    
    # Define the nodes
    @workflow.node
    def InputGateway(state: ExcelState) -> ExcelState:
        """Validate input and initialize the state."""
        logger.info("Excel Agent: Initializing workflow")
        
        if state.get("df") is None:
            return {"error": "No DataFrame provided"}
            
        if state.get("context") is None:
            return {"error": "No context provided"}
            
        if "template" not in state["context"]:
            return {"error": "No template specified in context"}
            
        return state
    
    @workflow.node
    def TemplateSelector(state: ExcelState) -> str:
        """Select the template based on context."""
        template_id = state["context"].get("template")
        logger.info(f"Excel Agent: Selected template {template_id}")
        return template_id
    
    @workflow.node
    def TemplateLoader(state: ExcelState) -> ExcelState:
        """Load the template workbook."""
        template_id = state["context"].get("template")
        try:
            result = tool_executor.execute(
                tool_name="load_template_wb",
                tool_input={"template_id": template_id}
            )
            return {**state, "wb": result}
        except Exception as e:
            logger.error(f"Error loading template: {str(e)}")
            return {**state, "error": f"Error loading template: {str(e)}"}
    
    @workflow.node
    def DataPreprocessor(state: ExcelState) -> ExcelState:
        """Preprocess data based on template requirements."""
        template_id = state["context"].get("template")
        try:
            # Use efficient DataFrame methods
            df_transformed = tool_executor.execute(
                tool_name="transform_df_for_template",
                tool_input={
                    "df": state["df"],
                    "template_id": template_id,
                    "context": state["context"]
                }
            )
            return {**state, "df": df_transformed}
        except Exception as e:
            logger.error(f"Error preprocessing data: {str(e)}")
            return {**state, "error": f"Error preprocessing data: {str(e)}"}
    
    @workflow.node
    def MapperFiller(state: ExcelState) -> ExcelState:
        """Map DataFrame to workbook cells."""
        template_id = state["context"].get("template")
        try:
            updated_wb = tool_executor.execute(
                tool_name="map_df_to_workbook",
                tool_input={
                    "df": state["df"],
                    "wb": state["wb"],
                    "template_id": template_id,
                    "context": state["context"]
                }
            )
            return {**state, "wb": updated_wb}
        except Exception as e:
            logger.error(f"Error mapping data to workbook: {str(e)}")
            return {**state, "error": f"Error mapping data to workbook: {str(e)}"}
    
    @workflow.node
    def WorkbookWriter(state: ExcelState) -> ExcelState:
        """Save workbook to bytes."""
        try:
            result = tool_executor.execute(
                tool_name="save_workbook",
                tool_input={
                    "wb": state["wb"],
                    "context": state["context"]
                }
            )
            return {
                **state, 
                "file_bytes": result["file_bytes"],
                "filename": result["filename"]
            }
        except Exception as e:
            logger.error(f"Error saving workbook: {str(e)}")
            return {**state, "error": f"Error saving workbook: {str(e)}"}
    
    @workflow.node
    def OutputDispatcher(state: ExcelState) -> ExcelResponse:
        """Prepare final response."""
        logger.info(f"Excel Agent: Completed workflow, generated file {state.get('filename')}")
        return ExcelResponse(
            file_bytes=state["file_bytes"],
            filename=state["filename"]
        )
    
    @workflow.node
    def ErrorHandler(state: ExcelState) -> Dict[str, Any]:
        """Handle errors in the workflow."""
        error_msg = state.get("error", "Unknown error")
        logger.error(f"Excel Agent error: {error_msg}")
        raise ValueError(error_msg)
    
    # Add edges
    workflow.add_edge(InputGateway, TemplateSelector)
    workflow.add_conditional_edges(
        TemplateSelector,
        condition=lambda s: s["context"]["template"],
        conditional_edge_funcs={
            "가": lambda _: TemplateLoader,
            "나": lambda _: TemplateLoader,
            "다": lambda _: TemplateLoader,
            "라": lambda _: TemplateLoader,
            "마": lambda _: TemplateLoader,
        },
        default_edge=lambda _: ErrorHandler
    )
    workflow.add_edge(TemplateLoader, DataPreprocessor)
    workflow.add_edge(DataPreprocessor, MapperFiller)
    workflow.add_edge(MapperFiller, WorkbookWriter)
    workflow.add_edge(WorkbookWriter, OutputDispatcher)
    workflow.add_edge(OutputDispatcher, END)
    workflow.add_edge(ErrorHandler, END)
    
    # Add conditional edge for error states
    workflow.add_conditional_edges(
        InputGateway,
        lambda s: "error" in s and s["error"] is not None,
        {
            True: ErrorHandler,
            False: TemplateSelector
        }
    )
    workflow.add_conditional_edges(
        TemplateLoader,
        lambda s: "error" in s and s["error"] is not None,
        {
            True: ErrorHandler,
            False: DataPreprocessor
        }
    )
    workflow.add_conditional_edges(
        DataPreprocessor,
        lambda s: "error" in s and s["error"] is not None,
        {
            True: ErrorHandler,
            False: MapperFiller
        }
    )
    workflow.add_conditional_edges(
        MapperFiller,
        lambda s: "error" in s and s["error"] is not None,
        {
            True: ErrorHandler,
            False: WorkbookWriter
        }
    )
    workflow.add_conditional_edges(
        WorkbookWriter,
        lambda s: "error" in s and s["error"] is not None,
        {
            True: ErrorHandler,
            False: OutputDispatcher
        }
    )
    
    # Compile
    return workflow.compile() 
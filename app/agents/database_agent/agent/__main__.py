# main.py
import os
import logging
from dotenv import load_dotenv

from app.common.server.server import A2AServer
from app.common.types import AgentCard, AgentCapabilities, AgentSkill
from app.common.utils.push_notification_auth import PushNotificationSenderAuth
from .task_manager import AgentTaskManager
from .agent import DBAgent

from fastapi import FastAPI
from starlette.responses import JSONResponse

# 1) Load environment variables & set up logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2) Generate JWK for push notifications
notification_sender_auth = PushNotificationSenderAuth()
notification_sender_auth.generate_jwk()

# 3) Define agent metadata
capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
skill = AgentSkill(
    id="text_to_sql",
    name="Text to SQL",
    description="Converts NL queries into SQL and runs them.",
    tags=["text-to-sql", "database"],
    examples=["Show me the top 5 customers by revenue"]
)
agent_card = AgentCard(
    name="Database Agent",
    description="NL→SQL agent",
    url="http://database-agent:10001/",
    version="1.0.0",
    defaultInputModes=DBAgent.SUPPORTED_CONTENT_TYPES,
    defaultOutputModes=DBAgent.SUPPORTED_CONTENT_TYPES,
    capabilities=capabilities,
    skills=[skill],
)

# 4) Create A2A server
server = A2AServer(
    agent_card=agent_card,
    task_manager=AgentTaskManager(
        agent=DBAgent(),
        notification_sender_auth=notification_sender_auth,
    ),
    host="0.0.0.0",
    port=10001,
)
a2a_app = server.app


app = FastAPI(title="Database Agent API")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from .router.query_router import router as query_router
app.include_router(query_router)

app.mount("/db_agent", a2a_app)